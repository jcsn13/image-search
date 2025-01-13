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
from vertexai.generative_models import GenerativeModel, Part
from dataclasses import dataclass
from typing import List
import os
from PIL import Image
import io
import base64
import json

@dataclass
class ImageAnalysis:
    """Container for image analysis results"""
    context_description: str
    visual_characteristics: List[str]
    object_annotations: List[str]
    location_context: str
    
    def to_combined_text(self) -> str:
        """Combine all analysis aspects into a single text"""
        response_string = f"""
        Contexto: {self.context_description}
        Elementos Visuais: {', '.join(self.visual_characteristics)}
        Objetos: {', '.join(self.object_annotations)}
        """

        if self.location_context:
            response_string += f"""
            Localização: {self.location_context}
            """

        return response_string.strip()

class GeminiImageAnalyzer:
    def __init__(self):
        """Initialize Gemini model"""
        self.model = GenerativeModel('gemini-1.5-pro')
        
        # Base configuration for all generations
        self.base_config = {
            "temperature": 0.2,
            "response_mime_type": "application/json"
        }
        
        # Specific configurations for different analysis types
        self.context_config = {
            **self.base_config,
            "max_output_tokens": 50,
            "response_schema": {
                "type": "OBJECT",
                "required": ["description"],
                "properties": {
                    "description": {"type": "STRING"}
                }
            }
        }
        
        self.visual_config = {
            **self.base_config,
            "max_output_tokens": 50,
            "response_schema": {
                "type": "OBJECT",
                "required": ["characteristics"],
                "properties": {
                    "characteristics": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                }
            }
        }
        
        self.object_config = {
            **self.base_config,
            "max_output_tokens": 50,
            "response_schema": {
                "type": "OBJECT",
                "required": ["objects"],
                "properties": {
                    "objects": {
                        "type": "ARRAY",
                        "items": {"type": "STRING"}
                    }
                }
            }
        }
    
    def _encode_image(self, image_path: str) -> str:
        """
        Convert image to base64 string
        
        Args:
            image_path: Path to image file
            
        Returns:
            Base64 encoded string of the image
        """
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            return base64.b64encode(img_byte_arr).decode('utf-8')
    
    def _parse_json_response(self, response_text: str) -> dict:
        """
        Parse the JSON response from the model
        
        Args:
            response_text: The raw text response from the model
            
        Returns:
            Parsed JSON dictionary
        """
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            print(f"Raw response: {response_text}")
            return {}
    
    def analyze_image(self, image_path: str, location_info: str = None) -> ImageAnalysis:
        """
        Analyze image using Gemini Pro
        
        Args:
            image_path: Path to image file
            location_info: Optional location information to analyze
            
        Returns:
            ImageAnalysis object containing analysis results
        """
        # Convert image to base64
        image_base64 = self._encode_image(image_path)
        
        # Generate context description
        context_response = self.model.generate_content([
            "Analise a imagem fornecida em base64 e forneça uma descrição detalhada do contexto e cena em apenas 1 frase curta.\n Para complementar sua análise também estou fornecendo informações de localidade da imagem: {location_info}",
            Part.from_data(image_base64, mime_type="image/png")
        ],
        generation_config=self.context_config)
        
        context_json = self._parse_json_response(context_response.text)
        context_description = context_json.get('description', '')
        
        # Generate visual characteristics
        visual_response = self.model.generate_content([
            "Analise a imagem fornecida em base64 e liste as principais características visuais, incluindo cores, iluminação, composição e estilo. Cada item da lista deve ser apenas 1 palavra, como uma tag para um aplicativo de busca.  No máximo 5 TAGs",
            Part.from_data(image_base64, mime_type="image/png")
        ],
        generation_config=self.visual_config)
        
        visual_json = self._parse_json_response(visual_response.text)
        visual_characteristics = visual_json.get('characteristics', [])
        
        # Generate object annotations
        object_response = self.model.generate_content([
            "Analise a imagem fornecida em base64 e liste os principais objetos e elementos visíveis. Cada item da lista deve ser apenas 1 palavra, como uma tag para um aplicativo de busca. No máximo 5 TAGs",
            Part.from_data(image_base64, mime_type="image/png")
        ],
        generation_config=self.object_config)
        
        object_json = self._parse_json_response(object_response.text)
        object_annotations = object_json.get('objects', [])
        
        # Process location information if provided
        location_context = None
        if location_info:
            location_context = location_info.get('components', [])
        
        return ImageAnalysis(
            context_description=context_description,
            visual_characteristics=visual_characteristics,
            object_annotations=object_annotations,
            location_context=location_context
        )