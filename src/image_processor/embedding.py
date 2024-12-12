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
from vertexai.vision_models import Image, MultiModalEmbeddingModel
import numpy as np
from typing import Optional
import os

class EmbeddingGenerator:
    def __init__(self):
        """Initialize multimodal embedding model"""
        self.project_id = os.environ.get('PROJECT_ID')
        self.location = os.environ.get('REGION')
        
        # Initialize Vertex AI
        vertexai.init(project=self.project_id, location=self.location)
        self.model = MultiModalEmbeddingModel.from_pretrained("multimodalembedding")
    
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
        # Load image using Vertex AI Image class
        image = Image.load_from_file(image_path)
        
        # Get embedding from model
        embeddings = self.model.get_embeddings(
            image=image,
            contextual_text=text_context if text_context else "",
            dimension=1408
        )
        
        # Convert to numpy and normalize
        embedding_array = np.array(embeddings.image_embedding)
        normalized_embedding = embedding_array / np.linalg.norm(embedding_array)
        
        return normalized_embedding