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

from flask import Flask, request, jsonify
import os
import logging
from vector_search import VectorSearchService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Initialize service
service = VectorSearchService()

@app.route('/search', methods=['POST'])
def search_by_text():
    """Search using text query"""
    try:
        data = request.get_json()
        
        if 'query' not in data:
            return jsonify({'error': 'No text query provided'}), 400

        query_text = data['query']
        num_results = data.get('num_results', 10)
        threshold = data.get('threshold', 0.5)

        # Generate embedding from text using multimodal model
        embedding = service.generate_text_embedding(query_text)

        # Search similar
        results = service.search_similar(
            query_embedding=embedding,
            num_neighbors=num_results,
            distance_threshold=threshold
        )

        # Format response
        response = {
            'query': query_text,
            'results': [
                {
                    'id': r.id,
                    'similarity_score': r.score,
                    'metadata': r.metadata
                } for r in results
            ]
        }

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing search request: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))