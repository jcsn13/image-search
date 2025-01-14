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
import numpy as np
from typing import Dict, Any, Tuple
import os
import json
import logging
import uuid

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
        
        # Initialize Firestore client
        self.db = firestore.Client()
        
        # Get the index name parts from the full resource name
        self.endpoint = aiplatform.MatchingEngineIndex(
            index_name=self.index_id
        )
        logger.info(f"Initialized endpoint with index: {self.endpoint.resource_name}")
    
    def _generate_id(self) -> str:
        """
        Generate a unique ID that's safe for both Firestore and Vector Search.
        
        Returns:
            A string containing a UUID4 without hyphens
        """
        return uuid.uuid4().hex
    
    def _extract_file_info(self, file_path: str) -> Tuple[str, str]:
        """
        Extract filename and directory path from full path.
        
        Args:
            file_path: Complete file path including directories
            
        Returns:
            Tuple of (filename, full_path)
        """
        filename = os.path.basename(file_path)
        return filename, file_path
    
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
    
    def _store_metadata_in_firestore(self, id: str, metadata: Dict[str, Any]) -> None:
        """
        Store metadata in Firestore
        
        Args:
            id: Generated unique identifier for the embedding
            metadata: Metadata to store
        """
        try:
            # Add timestamp to metadata
            metadata['created_at'] = firestore.SERVER_TIMESTAMP
            
            # Store in Firestore using the generated ID
            doc_ref = self.db.collection('index_metadata').document(id)
            doc_ref.set(metadata)
            logger.info(f"Stored metadata in Firestore for id: {id}")
            
        except Exception as e:
            logger.error(f"Error storing metadata in Firestore: {e}")
            raise
    
    def upsert_embedding(
        self,
        embedding: np.ndarray,
        file_path: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Upload embedding to Vector Search using streaming update and store metadata in Firestore
        
        Args:
            embedding: Normalized embedding vector
            file_path: Full path of the file
            metadata: Additional metadata to store
            
        Returns:
            The generated ID used for the embedding
        """
        try:
            # Generate a unique ID
            generated_id = self._generate_id()
            
            # Convert embedding to list if it's numpy array
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
            
            # Extract filename and keep full path in metadata
            filename, full_path = self._extract_file_info(file_path)
            metadata.update({
                'file_name': filename,
                'full_path': full_path
            })
            
            # Prepare data for backup storage
            storage_data = {
                "id": generated_id,
                "file_name": filename,
                "full_path": full_path,
                "embedding": embedding,
                "metadata": metadata
            }
            
            # Upload to GCS for backup
            blob_name = f"embeddings/{generated_id}.json"
            gcs_uri = self._upload_to_gcs(storage_data, blob_name)
            logger.info(f"Backed up embedding data to {gcs_uri}")
            
            # Store metadata in Firestore
            self._store_metadata_in_firestore(generated_id, metadata)
            
            # Prepare datapoint for streaming update
            datapoint = {
                "datapoint_id": generated_id,
                "feature_vector": embedding,
            }
            
            # Stream update to the index
            response = self.endpoint.upsert_datapoints(
                datapoints=[datapoint]
            )
            logger.info(f"Successfully streamed embedding with id: {generated_id}")
            
            return generated_id
            
        except Exception as e:
            logger.error(f"Error upserting embedding: {e}")
            raise