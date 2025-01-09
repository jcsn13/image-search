from typing import List, Dict
import random

def get_mock_results(query: str) -> List[Dict]:
    """
    Return mock search results for testing the UI
    """
    # List of realistic image categories
    categories = [
        ("nature", ["landscape", "mountain", "forest", "ocean", "sunset"]),
        ("urban", ["city", "architecture", "street", "building", "skyline"]),
        ("wildlife", ["animal", "bird", "mammal", "underwater", "safari"]),
        ("people", ["portrait", "crowd", "fashion", "sports", "lifestyle"]),
        ("food", ["cuisine", "restaurant", "cooking", "ingredients", "dishes"])
    ]
    
    # Generate 9 mock results (3x3 grid)
    mock_results = []
    for i in range(9):
        category, tags = random.choice(categories)
        similarity = round(random.uniform(0.60, 0.99), 2)
        
        result = {
            "image_path": f"/path/to/{category}/{i+1}.jpg",
            "image_url": f"https://picsum.photos/400/300?random={i}",  # Random placeholder image
            "similarity": similarity,
            "metadata": {
                "description": f"A beautiful {category} photograph",
                "tags": random.sample(tags, 3),
                "date_added": "2024-04-15",
                "size": "2.4 MB",
                "dimensions": "1920x1080"
            }
        }
        mock_results.append(result)
    
    # Sort by similarity by default
    mock_results.sort(key=lambda x: x['similarity'], reverse=True)
    return mock_results
