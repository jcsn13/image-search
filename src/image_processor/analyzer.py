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
from tenacity import retry, stop_after_attempt, wait_exponential
import logging

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
        self.logger = logging.getLogger(__name__)
        
        # List of regions to try
        self.regions = [
            "us-central1",
            "europe-west2",
            "europe-west3",
            "asia-northeast1",
            "australia-southeast1",
            "asia-south1"
        ]
        self._initialize_model()
        
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
    
    def _initialize_model(self, region: str = "us-central1") -> None:
        """Initialize model with specific region"""
        vertexai.init(project=os.getenv("GCP_PROJECT"), location=region)
        self.model = GenerativeModel('gemini-1.5-pro')
    
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def _generate_with_fallback(self, prompt, config):
        """Generate content with region fallback"""
        last_error = None
        
        for region in self.regions:
            try:
                self._initialize_model(region)
                response = self.model.generate_content(prompt, generation_config=config)
                return self._parse_json_response(response.text)
            except Exception as e:
                self.logger.warning(f"Error in region {region}: {str(e)}")
                last_error = e
                continue
                
        raise Exception(f"All regions failed. Last error: {str(last_error)}")
    
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
        Analyze image using Gemini Pro with retries and region fallback
        """
        # Convert image to base64
        image_base64 = self._encode_image(image_path)
        
        # Generate context description
        context_prompt = [
            "Analise a imagem fornecida em base64 e forneça uma descrição detalhada do contexto e cena em apenas 1 frase curta.\n Para complementar sua análise também estou fornecendo informações de localidade da imagem: {location_info}",
            Part.from_data(image_base64, mime_type="image/png")
        ]
        context_json = self._generate_with_fallback(context_prompt, self.context_config)
        context_description = context_json.get('description', '')
        
        # Generate visual characteristics
        visual_prompt = [
            "Analise a imagem fornecida em base64 e liste as principais características visuais, incluindo cores, iluminação, composição e estilo. Cada item da lista deve ser apenas 1 palavra, como uma tag para um aplicativo de busca.  No máximo 5 TAGs",
            Part.from_data(image_base64, mime_type="image/png")
        ]
        visual_json = self._generate_with_fallback(visual_prompt, self.visual_config)
        visual_characteristics = visual_json.get('characteristics', [])
        
        # Generate object annotations
        object_prompt = [
            "Analise a imagem fornecida em base64 e liste os principais objetos e elementos visíveis. Cada item da lista deve ser apenas 1 palavra, como uma tag para um aplicativo de busca. No máximo 5 TAGs",
            Part.from_data(image_base64, mime_type="image/png")
        ]
        object_json = self._generate_with_fallback(object_prompt, self.object_config)
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