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
import numpy as np
from typing import Dict, Any
import os
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorSearchClient:
    def __init__(self):
        """Initialize Vector Search client"""
        self.project_id = os.environ.get('PROJECT_ID')
        self.location = os.environ.get('REGION')
        self.bucket_name = os.environ.get('PROCESSED_BUCKET')
        self.index_id = os.environ.get('VECTOR_SEARCH_INDEX')
        
        if not all([self.project_id, self.location, self.index_id, self.bucket_name]):
            raise ValueError(
                "Missing required environment variables. "
                "Please set PROJECT_ID, REGION, INDEX_ID, and BUCKET_NAME"
            )
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.project_id,
            location=self.location
        )
        
        # Initialize storage client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        # Initialize the index
        self.index = aiplatform.MatchingEngineIndex(
            index_name=self.index_id
        )
        logger.info(f"Initialized index: {self.index.resource_name}")
    
    def _upload_to_gcs(self, data: Dict[str, Any], blob_name: str) -> str:
        """
        Upload data to GCS
        
        Args:
            data: Data to upload
            blob_name: Name for the blob
            
        Returns:
            GCS URI for the uploaded file
        """
        blob = self.bucket.blob(blob_name)
        blob.upload_from_string(
            data=json.dumps(data),
            content_type='application/json'
        )
        return f"gs://{self.bucket_name}/{blob_name}"
    
    def upsert_embedding(
        self,
        embedding: np.ndarray,
        id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Upload embedding to Vector Search
        
        Args:
            embedding: Normalized embedding vector
            id: Unique identifier for the embedding
            metadata: Additional metadata to store
        """
        try:
            # Convert embedding to list if it's numpy array
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            # Prepare data for upload
            data = [{
                "id": id,
                "embedding": embedding,
                # "name": metadata["processed_image_path"]
            }]
            
            # Upload to GCS
            blob_name = f"embeddings/{id}.json"
            gcs_uri = self._upload_to_gcs(data, blob_name)
            logger.info(f"Uploaded embedding data to {gcs_uri}")
            
            # Update the index embeddings
            self.index.update_embeddings(
                contents_delta_uri=f"gs://{self.bucket_name}/embeddings",
                is_complete_overwrite=False
            )
            logger.info(f"Successfully updated index with embedding id: {id}")
            
        except Exception as e:
            logger.error(f"Error upserting embedding: {e}")
            raise