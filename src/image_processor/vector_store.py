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
import numpy as np
from typing import Dict, List, Any
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorSearchClient:
    def __init__(self):
        """Initialize Vector Search client"""
        self.project_id = os.environ.get('PROJECT_ID')
        self.location = os.environ.get('REGION')
        
        if not all([self.project_id, self.location]):
            raise ValueError(
                "Missing required environment variables. "
                "Please set PROJECT_ID and REGION"
            )
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.project_id,
            location=self.location
        )
        
        # Get first index endpoint from the list
        index_endpoints = aiplatform.MatchingEngineIndexEndpoint.list()
        
        # Log all endpoints
        logger.info("Available index endpoints:")
        for ep in index_endpoints:
            logger.info(f"- Name: {ep.display_name}")
            logger.info(f"  Resource name: {ep.resource_name}")
            logger.info(f"  Deployed indexes: {len(ep.deployed_indexes)}")
            
        if not index_endpoints:
            raise ValueError("No index endpoints found")
            
        self.endpoint = aiplatform.MatchingEngineIndexEndpoint(
            index_endpoint_name=index_endpoints[0].resource_name
        )
        logger.info(f"Using endpoint: {self.endpoint.display_name}")
    
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
        # Convert embedding to list if it's numpy array
        if isinstance(embedding, np.ndarray):
            embedding = embedding.tolist()
            
        # Make the request
        try:
            self.endpoint.upsert_datapoints(
                embeddings=[embedding],
                ids=[id],
                restricts=[metadata]
            )
            logger.info(f"Successfully upserted embedding with id: {id}")
        except Exception as e:
            logger.error(f"Error upserting embedding: {e}")
            raise