"""
Copyright 2024 Google LLC

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from google.cloud import aiplatform
from google.cloud import storage
from google.cloud import firestore
import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel
import numpy as np
import os
from typing import List
import logging
import json
from models import SearchResult

logger = logging.getLogger(__name__)

class VectorSearchService:
    def __init__(self):
        """Initialize Vector Search service"""
        self.project_id = os.environ.get('PROJECT_ID')
        self.location = os.environ.get('REGION')
        self.index_id = os.environ.get('VECTOR_SEARCH_INDEX')
        self.bucket_name = os.environ.get('PROCESSED_BUCKET')
        self.deployed_index_id = os.environ.get('DEPLOYED_INDEX_ID')

        if not all([self.project_id, self.location, self.index_id]):
            raise ValueError(
                "Missing required environment variables. "
                "Please set PROJECT_ID, REGION, and VECTOR_SEARCH_INDEX"
            )

        # Initialize Vertex AI
        vertexai.init(
            project=self.project_id,
            location=self.location
        )

        # Initialize Vector Search index
        self.index = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=self.deployed_index_id.split("/deployedIndex")[0]
        )
        
        # Initialize multimodal embedding model
        self.embedding_model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
        
        # Initialize storage client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)

        # Initialize Firestore client
        self.db = firestore.Client()

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for text query using multimodal model"""
        embeddings = self.embedding_model.get_embeddings(
            image=None,  # No image for text-only query
            contextual_text=text,
            dimension=1408
        )
        
        # Get text embedding from model response
        embedding_array = np.array(embeddings.text_embedding)
        return embedding_array / np.linalg.norm(embedding_array)

    async def _get_metadata_from_firestore(self, doc_id: str) -> dict:
        """Get metadata from Firestore for a given document ID"""
        try:
            doc_ref = self.db.collection('index_metadata').document(doc_id)
            doc = doc_ref.get()
            if doc.exists:
                return doc.to_dict()
            else:
                logger.warning(f"No metadata found in Firestore for document ID: {doc_id}")
                return {}
        except Exception as e:
            logger.error(f"Error fetching metadata from Firestore for {doc_id}: {e}")
            return {}

    def search_similar(
            self,
            query_embedding: np.ndarray,
            num_neighbors: int = 10,
            distance_threshold: float = 0.0
        ) -> List[SearchResult]:
            """Search for similar vectors"""
            try:
                # Convert embedding to list if it's numpy array
                if isinstance(query_embedding, np.ndarray):
                    query_embedding = query_embedding.tolist()

                # Query the index endpoint
                response = self.index.find_neighbors(
                    deployed_index_id="deployed_image_search_index",
                    queries=[query_embedding],
                    num_neighbors=num_neighbors
                )

                results = []
                # Process the nearest neighbors - response is a list and [0] contains the neighbors for our query
                for neighbor in response[0]:
                    # Skip results above distance threshold
                    distance = neighbor.distance
                    if distance > distance_threshold:
                        continue

                    # Get metadata from Firestore using the neighbor.id
                    doc_ref = self.db.collection('index_metadata').document(neighbor.id)
                    doc = doc_ref.get()
                    
                    if doc.exists:
                        metadata = doc.to_dict()
                    else:
                        logger.warning(f"No metadata found in Firestore for document ID: {neighbor.id}")
                        metadata = {}

                    results.append(SearchResult(
                        id=neighbor.id,
                        score=1.0 - distance,  # Convert distance to similarity score
                        metadata=metadata
                    ))

                return results

            except Exception as e:
                logger.error(f"Error searching similar vectors: {e}", exc_info=True)
                raise