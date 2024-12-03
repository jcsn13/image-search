from google.cloud import aiplatform
import numpy as np
from typing import Dict, List, Any
import os

class VectorSearchClient:
    def __init__(self):
        """Initialize Vector Search client"""
        self.project_id = os.environ.get('PROJECT_ID')
        self.region = os.environ.get('REGION')
        self.index_id = os.environ.get('VECTOR_SEARCH_INDEX_ID')
        
        # Initialize Vertex AI
        aiplatform.init(
            project=self.project_id,
            location=self.region
        )
        
        # Get index endpoint
        self.index = aiplatform.MatchingEngineIndex(
            index_name=self.index_id
        )
    
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
        self.index.upsert_embeddings(
            embeddings=[embedding],
            ids=[id],
            metadata_list=[metadata]
        )