from google.cloud import aiplatform
import numpy as np
from typing import Optional
import base64

class EmbeddingGenerator:
    def __init__(self):
        """Initialize multimodal embedding model"""
        self.model = aiplatform.MultimodalEmbeddingModel.from_pretrained(
            "multimodal-embedding@001"
        )
    
    def _encode_image(self, image_path: str) -> str:
        """Convert image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()
    
    def generate_embedding(
        self,
        image_path: str,
        text_context: Optional[str] = None
    ) -> np.ndarray:
        """
        Generate embedding for image and optional text
        
        Args:
            image_path: Path to image file
            text_context: Optional text context
            
        Returns:
            Normalized embedding vector
        """
        # Encode image
        image_bytes = self._encode_image(image_path)
        
        # Get embedding from model
        embedding = self.model.get_embeddings(
            image=image_bytes,
            text=text_context if text_context else ""
        )
        
        # Convert to numpy and normalize
        embedding_array = np.array(embedding.image_embedding)
        normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
        
        return normalized_embedding