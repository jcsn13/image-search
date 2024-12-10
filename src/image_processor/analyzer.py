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
from vertexai.preview import generative_models
from dataclasses import dataclass
from typing import List
import os
from PIL import Image

@dataclass
class ImageAnalysis:
    """Container for image analysis results"""
    context_description: str
    visual_characteristics: str
    object_annotations: List[str]
    
    def to_combined_text(self) -> str:
        """Combine all analysis aspects into a single text"""
        return f"""
        Context: {self.context_description}
        Visual Elements: {self.visual_characteristics}
        Key Objects: {', '.join(self.object_annotations)}
        """.strip()

class GeminiImageAnalyzer:
    def __init__(self):
        """Initialize Gemini model"""
        self.model = generative_models.GenerativeModel('gemini-pro-vision')
    
    def analyze_image(self, image_path: str) -> ImageAnalysis:
        """
        Analyze image using Gemini Vision
        
        Args:
            image_path: Path to image file
            
        Returns:
            ImageAnalysis object containing analysis results
        """
        image = Image.open(image_path)
        
        # Generate context description
        context_response = self.model.generate_content([
            "Provide a detailed description of this image's context and scene in 2-3 sentences.",
            image
        ])
        context_description = context_response.text
        
        # Generate visual characteristics
        visual_response = self.model.generate_content([
            "List the key visual characteristics including colors, lighting, composition, and style. Provide as comma-separated list.",
            image
        ])
        visual_characteristics = visual_response.text
        
        # Generate object annotations
        object_response = self.model.generate_content([
            "List the main objects and elements visible in this image. Provide as comma-separated list.",
            image
        ])
        object_annotations = [obj.strip() for obj in object_response.text.split(',')]
        
        return ImageAnalysis(
            context_description=context_description,
            visual_characteristics=visual_characteristics,
            object_annotations=object_annotations
        )