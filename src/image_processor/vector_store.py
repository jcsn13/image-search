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
                "Please set PROJECT_ID, REGION, VECTOR_SEARCH_INDEX, and BUCKET_NAME"
            )
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.project_id,
            location=self.location
        )
        
        # Initialize storage client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(self.bucket_name)
        
        # Get the index name parts from the full resource name
        self.endpoint = aiplatform.MatchingEngineIndex(
            index_name=self.index_id
        )
        logger.info(f"Initialized endpoint with index: {self.endpoint.resource_name}")
    
    def _upload_to_gcs(self, data: Dict[str, Any], blob_name: str) -> str:
        """
        Upload data to GCS for backup/record keeping
        
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
        Upload embedding to Vector Search using streaming update
        
        Args:
            embedding: Normalized embedding vector
            id: Unique identifier for the embedding
            metadata: Additional metadata to store
        """
        try:
            # Convert embedding to list if it's numpy array
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            # Prepare data for backup storage
            storage_data = {
                "id": id,
                "embedding": embedding,
                "metadata": metadata
            }
            
            # Upload to GCS for backup
            blob_name = f"embeddings/{id}.json"
            gcs_uri = self._upload_to_gcs(storage_data, blob_name)
            logger.info(f"Backed up embedding data to {gcs_uri}")
            
            # Prepare datapoint for streaming update
            datapoint = {
                "datapoint_id": id,
                "feature_vector": embedding,
            }
            
            # # Add metadata as feature fields
            # restricted_keys = ['file_name', 'original_bucket', 'processed_image_path', 
            #                  'context', 'characteristics', 'objects']
            # for key in restricted_keys:
            #     if key in metadata:
            #         datapoint[f"metadata_{key}"] = str(metadata[key])
            
            # Stream update to the index
            response = self.endpoint.upsert_datapoints(
                datapoints=[datapoint]
            )
            logger.info(f"Successfully streamed embedding with id: {id}")
            
        except Exception as e:
            logger.error(f"Error upserting embedding: {e}")
            raise