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

import vertexai
from vertexai.vision_models import MultiModalEmbeddingModel
import numpy as np
from typing import Optional
import base64
from PIL import Image

class EmbeddingGenerator:
    def __init__(self):
        """Initialize multimodal embedding model"""
        # Initialize Vertex AI
        self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding@001")
    
    def _encode_image(self, image_path: str) -> Image:
        """Load image from path"""
        return Image.open(image_path)
    
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
        # Load image
        image = self._encode_image(image_path)
        
        # Get embedding from model
        embedding = self.model.get_embeddings(
            image=image,
            text=text_context if text_context else ""
        )
        
        # Convert to numpy and normalize
        embedding_array = np.array(embedding.image_embedding)
        normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
        
        return normalized_embedding