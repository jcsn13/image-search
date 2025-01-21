import streamlit as st
import requests
from typing import List, Dict
import os
from dotenv import load_dotenv
from io import BytesIO
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from google.cloud import storage
from datetime import timedelta
import google.auth
from google.auth import compute_engine, impersonated_credentials
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials as OAuth2Credentials

# Load environment variables
load_dotenv()

# Set page config for a wider layout
st.set_page_config(
    page_title="Image Search",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Material Design styling
st.markdown("""
    <style>
    /* Material Design Colors and Variables */
    :root {
        --md-primary: #1976D2;
        --md-primary-light: #2196F3;
        --md-surface: #FFFFFF;
        --md-background: #FAFAFA;
        --md-on-surface: #212121;
        --md-elevation-1: 0 2px 4px -1px rgba(0,0,0,0.2), 0 4px 5px 0 rgba(0,0,0,0.14), 0 1px 10px 0 rgba(0,0,0,0.12);
        --md-elevation-2: 0 3px 5px -1px rgba(0,0,0,0.2), 0 6px 10px 0 rgba(0,0,0,0.14), 0 1px 18px 0 rgba(0,0,0,0.12);
    }

    /* Global Styles */
    .stApp {
        background-color: var(--md-background);
    }

    /* Search Container */
    .search-container {
        background-color: var(--md-surface);
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: var(--md-elevation-1);
        margin: 1rem 0 2rem 0;
    }

    /* Image Cards */
    .stImage {
        border-radius: 8px;
        transition: transform 0.2s;
        margin-bottom: 0.5rem;
    }

    .stImage:hover {
        transform: scale(1.02);
    }

    /* Make progress bars more compact */
    .stProgress {
        margin-bottom: 0.5rem !important;
    }

    /* Make expanders more compact */
    .streamlit-expanderHeader {
        margin-top: 0 !important;
        margin-bottom: 0.5rem !important;
        padding: 0.5rem !important;
    }

    /* Typography */
    h1, h2, h3 {
        font-family: 'Roboto', sans-serif;
        color: var(--md-on-surface);
        font-weight: 500;
    }

    /* Input Fields */
    .stTextInput > div > div {
        border-radius: 4px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 4px;
        box-shadow: var(--md-elevation-1);
        transition: box-shadow 0.2s;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    .stButton > button:hover {
        box-shadow: var(--md-elevation-2);
    }

    /* Expander */
    .streamlit-expanderHeader {
        background-color: var(--md-surface);
        border-radius: 4px;
        border: none;
        box-shadow: var(--md-elevation-1);
    }

    /* Sidebar */
    .css-1d391kg {
        background-color: var(--md-surface);
    }

    /* Results Counter */
    .results-count {
        background-color: var(--md-surface);
        padding: 0.5rem 1rem;
        border-radius: 4px;
        box-shadow: var(--md-elevation-1);
        display: inline-block;
        margin-bottom: 1rem;
    }

    /* Tags */
    .tag {
        background-color: #E3F2FD;
        color: var(--md-primary);
        padding: 2px 6px;
        border-radius: 12px;
        font-size: 0.75rem;
        margin-right: 4px;
        margin-bottom: 2px;
        display: inline-block;
    }

    /* Compact the metadata text */
    .metadata-text {
        font-size: 0.9rem;
        margin: 0;
        padding: 0;
    }

    /* Pagination Controls */
    .pagination-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem 0;
        gap: 1rem;
    }
    
    .pagination-info {
        background-color: var(--md-surface);
        padding: 0.5rem 1rem;
        border-radius: 4px;
        box-shadow: var(--md-elevation-1);
    }

    /* Image Grid */
    .image-grid {
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 1rem;
        padding: 1rem;
    }

    .image-card {
        background: var(--md-surface);
        border-radius: 8px;
        box-shadow: var(--md-elevation-1);
        overflow: hidden;
        height: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

# Constants
API_ENDPOINT = os.getenv('API_ENDPOINT')
if not API_ENDPOINT:
    raise ValueError("API_ENDPOINT environment variable is not set")

# Initialize storage client at app startup
storage_client = storage.Client()

def get_signed_url(bucket_name: str, blob_name: str, expiration: int = 3600) -> str:
    """Generate signed URL for accessing private bucket objects"""
    try:
        credentials, project = google.auth.default()
        storage_client = storage.Client(credentials=credentials)
        
        # If using OAuth credentials (local development with gcloud auth)
        if isinstance(credentials, OAuth2Credentials):
            url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
            if credentials.token:
                url = f"{url}?access_token={credentials.token}"
            return url
            
        # If using Compute Engine credentials (Cloud Run)
        elif isinstance(credentials, compute_engine.Credentials):
            try:
                # First try to generate a signed URL
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                return blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(seconds=expiration),
                    method="GET"
                )
            except Exception as e:
                st.write(f"Falling back to token auth: {str(e)}")
                # Fall back to token auth if signing fails
                credentials = compute_engine.IDTokenCredentials(
                    credentials, "https://storage.googleapis.com"
                )
                url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
                if credentials.token:
                    url = f"{url}?access_token={credentials.token}"
                return url
            
        # If using service account credentials
        elif isinstance(credentials, service_account.Credentials):
            bucket = storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            try:
                return blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(seconds=expiration),
                    method="GET"
                )
            except Exception as e:
                st.write(f"Signed URL generation failed, using direct access: {str(e)}")
                return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
                
        # If using impersonated credentials
        elif isinstance(credentials, impersonated_credentials.Credentials):
            try:
                # Create a source credentials object that can sign
                source_credentials = service_account.Credentials.from_service_account_file(
                    'key.json',  # Your service account key file
                    scopes=['https://www.googleapis.com/auth/cloud-platform']
                )
                
                # Create the storage client with the source credentials
                storage_client = storage.Client(credentials=source_credentials)
                bucket = storage_client.bucket(bucket_name)
                blob = bucket.blob(blob_name)
                
                # Generate signed URL with the source credentials
                return blob.generate_signed_url(
                    version="v4",
                    expiration=timedelta(seconds=expiration),
                    method="GET",
                    service_account_email=source_credentials.service_account_email
                )
            except Exception as e:
                st.error(f"Signed URL generation failed with impersonated credentials: {str(e)}")
                try:
                    # Try to use the credentials token directly
                    headers = {}
                    auth_req = google.auth.transport.requests.Request()
                    credentials.refresh(auth_req)
                    credentials.apply(headers)
                    
                    if 'authorization' in headers:
                        token = headers['authorization'].split(' ')[1]
                        url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}?access_token={token}"
                        return url
                except Exception as token_error:
                    st.error(f"Token-based access also failed: {str(token_error)}")
                    return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
            
        else:
            st.error(f"Unsupported credentials type: {type(credentials)}")
            return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
            
    except Exception as e:
        st.error(f"Error generating URL: {str(e)}")
        return f"https://storage.googleapis.com/{bucket_name}/{blob_name}"

def search_images(query: str, use_mock: bool = False):
    """
    Search for images using either the real API or mock data.
    Returns the full response object when using the real API,
    or a mock response object when using mock data.
    """
    if use_mock:
        mock_results = [
            {
                "id": "city-building.jpg",
                "metadata": {
                    "characteristics": "Modern, urban, architectural, glass, steel, blue sky, reflective, downtown",
                    "content_type": "image/jpeg",
                    "context": "A modern glass skyscraper in a downtown area, reflecting the blue sky and surrounding buildings. The architecture showcases contemporary urban design.",
                    "created_at": "Fri, 10 Jan 2025 12:35:36 GMT",
                    "file_name": "city-building.jpg",
                    "location": "New York",
                    "objects": "Building, windows, sky, reflections, architectural details, glass panels",
                    "original_bucket": "image-search-demo",
                    "processed_image_path": "https://images.unsplash.com/photo-1486325212027-8081e485255e?w=800&auto=format&fit=crop",
                    "size": "3.2 MB"
                },
                "similarity_score": 0.9415058791637421
            },
            {
                "id": "nature-landscape.jpg",
                "metadata": {
                    "characteristics": "Natural, mountainous, scenic, green, peaceful, outdoor, wilderness, majestic",
                    "content_type": "image/jpeg",
                    "context": "A breathtaking mountain landscape with lush green valleys and snow-capped peaks. The scene captures the raw beauty of nature in its most pristine form.",
                    "created_at": "Fri, 10 Jan 2025 12:35:19 GMT",
                    "file_name": "nature-landscape.jpg",
                    "location": "Swiss Alps",
                    "objects": "Mountains, trees, valley, sky, clouds, snow peaks, forest",
                    "original_bucket": "image-search-demo",
                    "processed_image_path": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=800&auto=format&fit=crop",
                    "size": "2.8 MB"
                },
                "similarity_score": 0.9819442108273506
            },
            {
                "id": "coffee-workspace.jpg",
                "metadata": {
                    "characteristics": "Indoor, warm, cozy, productive, modern, minimal, organized, professional",
                    "content_type": "image/jpeg",
                    "context": "A clean and modern workspace setup with a laptop, coffee cup, and minimal accessories on a wooden desk. The scene suggests a productive work environment.",
                    "created_at": "Fri, 10 Jan 2025 12:34:45 GMT",
                    "file_name": "coffee-workspace.jpg",
                    "location": "Home Office",
                    "objects": "Laptop, coffee cup, desk, notebook, pen, plant, wooden surface",
                    "original_bucket": "image-search-demo",
                    "processed_image_path": "https://images.unsplash.com/photo-1486312338219-ce68d2c6f44d?w=800&auto=format&fit=crop",
                    "size": "1.9 MB"
                },
                "similarity_score": 0.8756324159276485
            },
            {
                "id": "beach-sunset.jpg",
                "metadata": {
                    "characteristics": "Natural, coastal, warm colors, peaceful, scenic, romantic, tropical, serene",
                    "content_type": "image/jpeg",
                    "context": "A stunning sunset view at a tropical beach with palm trees silhouetted against the orange and purple sky. The ocean reflects the warm colors of the setting sun.",
                    "created_at": "Fri, 10 Jan 2025 12:33:22 GMT",
                    "file_name": "beach-sunset.jpg",
                    "location": "Tropical Beach",
                    "objects": "Ocean, beach, palm trees, sun, clouds, sand, waves",
                    "original_bucket": "image-search-demo",
                    "processed_image_path": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=800&auto=format&fit=crop",
                    "size": "2.4 MB"
                },
                "similarity_score": 0.9234567890123456
            },
            {
                "id": "food-photography.jpg",
                "metadata": {
                    "characteristics": "Culinary, colorful, appetizing, fresh, styled, professional, detailed, artistic",
                    "content_type": "image/jpeg",
                    "context": "An artistically arranged plate of fresh food showcasing culinary expertise. The composition includes vibrant vegetables and carefully plated elements.",
                    "created_at": "Fri, 10 Jan 2025 12:32:15 GMT",
                    "file_name": "food-photography.jpg",
                    "location": "Studio",
                    "objects": "Plate, food, vegetables, garnish, table, cutlery, herbs",
                    "original_bucket": "image-search-demo",
                    "processed_image_path": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=800&auto=format&fit=crop",
                    "size": "1.7 MB"
                },
                "similarity_score": 0.8912345678901234
            }
        ]
        
        # Create a mock response object
        class MockResponse:
            def __init__(self, data):
                self.data = data
                self.status_code = 200
                self.ok = True
                self._headers = {
                    'content-type': 'application/json',
                    'date': 'Fri, 10 Jan 2025 13:54:00 GMT',
                    'server': 'Mock Server'
                }
            
            def json(self):
                return self.data
            
            @property
            def headers(self):
                return self._headers
            
            @property
            def text(self):
                return str(self.data)
        
        return MockResponse({'query': query, 'results': mock_results})
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{API_ENDPOINT}/search",
            headers=headers,
            json={"query": query}
        )
        return response
    except requests.RequestException as e:
        # Create an error response
        class ErrorResponse:
            def __init__(self, error):
                self.status_code = 500
                self.ok = False
                self.error = error
                self._headers = {}
            
            def json(self):
                return {'error': str(self.error)}
            
            @property
            def headers(self):
                return self._headers
            
            @property
            def text(self):
                return str(self.error)
        
        return ErrorResponse(e)

def clamp(value, min_val=0.0, max_val=1.0):
    """Clamp a value between min and max values."""
    return max(min_val, min(value, max_val))

def init_session_state():
    """Initialize session state variables"""
    if 'search_performed' not in st.session_state:
        st.session_state.search_performed = False
    if 'total_results' not in st.session_state:
        st.session_state.total_results = 0
    if 'query' not in st.session_state:
        st.session_state.query = ""
    if 'current_results' not in st.session_state:
        st.session_state.current_results = []
    if 'max_results' not in st.session_state:
        st.session_state.max_results = 20

def reset_search_state():
    """Reset search-related state when performing a new search"""
    st.session_state.search_performed = True
    st.session_state.current_results = []
    st.session_state.total_results = 0

def min_max_scale(scores):
    """
    Normalize scores using min-max scaling.
    Returns a value between 0 and 1.
    """
    min_score = min(scores)
    max_score = max(scores)
    if max_score == min_score:
        return [1.0] * len(scores)  # If all scores are equal, return 1.0
    return [(x - min_score) / (max_score - min_score) for x in scores]

def main():
    # Initialize session state
    init_session_state()
    
    # Sidebar for settings
    with st.sidebar:
        st.title("⚙️ Settings")
        use_mock = st.toggle("Use mock data", value=False)
        st.divider()
        st.markdown("### Display Settings")
        # Add maximum results selector
        max_results = st.select_slider(
            "Maximum results to display",
            options=[5, 10, 20, 50, 100],
            value=st.session_state.max_results,
            key="max_results_slider",
            help="Select how many results to show"
        )
        
        # Update max results if changed
        if max_results != st.session_state.max_results:
            st.session_state.max_results = max_results
            st.rerun()
            
        st.divider()
        sort_by = st.selectbox("Sort results by", 
                             ["Similarity", "Date", "Name"],
                             help="Choose how to sort the search results")
    
    # Main content
    st.title("🔍 Image Search")
    
    # Search container
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input("", 
                                placeholder="Search images by description or content...",
                                key="search_input",
                                label_visibility="collapsed")
        with col2:
            search_button = st.button("Search", type="primary", use_container_width=True)
    
    # Create tabs for results and logging
    results_tab, logging_tab = st.tabs(["Results", "Logging"])
    
    # Handle search
    if search_button and query:
        # Reset search state for new queries
        if query != st.session_state.query:
            reset_search_state()
            st.session_state.query = query
            
        with st.spinner("🔍 Searching for images..."):
            response = search_images(query, use_mock=use_mock)
            
            # Show response details in logging tab
            with logging_tab:
                st.subheader("Response Details")
                st.write("Response Status:", response.status_code)
                st.write("Response Headers:", dict(response.headers))
                try:
                    st.json(response.json())
                except requests.exceptions.JSONDecodeError:
                    st.error("Could not decode JSON response")
                    st.text("Raw Response:")
                    st.text(response.text)
            
            with results_tab:
                if response.ok:
                    results = response.json().get('results', [])
                    
                    if results:
                        # Update current results directly
                        st.session_state.current_results = results
                        st.session_state.total_results = len(results)
                        
                        display_results = st.session_state.current_results
                        
                        # Sort results
                        if sort_by == "Similarity":
                            display_results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
                        elif sort_by == "Date":
                            display_results.sort(
                                key=lambda x: x.get('metadata', {}).get('created_at', ''),
                                reverse=True
                            )
                        elif sort_by == "Name":
                            display_results.sort(
                                key=lambda x: x.get('metadata', {}).get('file_name', '').lower()
                            )
                        
                        # Limit results based on user selection
                        total_results = len(display_results)
                        display_results = display_results[:st.session_state.max_results]
                        
                        # Display results count with material design
                        st.markdown(f"""
                            <div class="results-count">
                                📸 Showing {len(display_results)} of {total_results} images
                            </div>
                            """, 
                            unsafe_allow_html=True
                        )
                        
                        # Calculate normalized scores for all results
                        similarity_scores = [result.get('similarity_score', 0) for result in display_results]
                        normalized_scores = min_max_scale(similarity_scores)
                        
                        # Create grid layout with 5 columns for better alignment
                        cols = st.columns(5)
                        for idx, (result, normalized_score) in enumerate(zip(display_results, normalized_scores)):
                            with cols[idx % 5]:
                                with st.container():
                                    placeholder = st.empty()
                                    with placeholder:
                                        st.spinner("Loading image...")  # Shows while image loads
                                    # Get image URL from processed_image_path
                                    image_url = result.get('metadata', {}).get('processed_image_path', '')
                                    if image_url.startswith('gs://'):
                                        # Parse bucket and blob name from GCS path
                                        bucket_name = image_url.split('/')[2]
                                        blob_name = '/'.join(image_url.split('/')[3:])
                                        try:
                                            # Generate signed URL for private bucket access
                                            image_url = get_signed_url(bucket_name, blob_name)
                                        except Exception as e:
                                            st.error(f"Error generating signed URL: {str(e)}")
                                            continue
                                    
                                    try:
                                        # Load image from URL
                                        response = requests.get(image_url)
                                        if response.status_code == 200:
                                            image_bytes = BytesIO(response.content)
                                            # Image card with hover effect
                                            st.image(
                                                image_bytes,
                                                use_container_width=True
                                            )
                                        else:
                                            st.error(f"Failed to load image: {response.status_code}")
                                    except Exception as e:
                                        st.error(f"Error loading image: {str(e)}")
                                    
                                    # Display both raw and normalized similarity scores
                                    raw_similarity = result.get('similarity_score', 0)
                                    st.progress(normalized_score, 
                                              text=f"Similarity: {raw_similarity:.3f} (Normalized: {normalized_score:.0%})")
                                    
                                    # Metadata expansion
                                    with st.expander("Details"):
                                        metadata = result.get('metadata', {})
                                        
                                        if metadata:
                                            st.markdown('<p class="metadata-text"><strong>Context</strong></p>', unsafe_allow_html=True)
                                            st.markdown(f'<p class="metadata-text">{metadata.get("context", "N/A")}</p>', unsafe_allow_html=True)
                                            
                                            st.markdown('<p class="metadata-text"><strong>Characteristics</strong></p>', unsafe_allow_html=True)
                                            characteristics = metadata.get('characteristics', [])
                                            if isinstance(characteristics, str):  # Handle legacy format
                                                characteristics = characteristics.split(',')
                                            tags_html = " ".join([
                                                f'<span class="tag">{tag.strip()}</span>' 
                                                for tag in characteristics if tag and isinstance(tag, str)
                                            ])
                                            st.markdown(tags_html, unsafe_allow_html=True)
                                            
                                            st.markdown('<p class="metadata-text"><strong>Objects</strong></p>', unsafe_allow_html=True)
                                            objects = metadata.get('objects', [])
                                            if isinstance(objects, str):  # Handle legacy format
                                                objects = objects.split(',')
                                            objects_html = " ".join([
                                                f'<span class="tag">{obj.strip()}</span>'
                                                for obj in objects if obj and isinstance(obj, str)
                                            ])
                                            st.markdown(objects_html, unsafe_allow_html=True)
                                            
                                            st.markdown('<p class="metadata-text"><strong>Properties</strong></p>', unsafe_allow_html=True)
                                            col1, col2 = st.columns(2)
                                            with col1:
                                                st.markdown(f'<p class="metadata-text">Type: {metadata.get("content_type", "N/A")}</p>', unsafe_allow_html=True)
                                            with col2:
                                                st.markdown(f'<p class="metadata-text">Created: {metadata.get("created_at", "N/A")}</p>', unsafe_allow_html=True)
                    else:
                        st.warning("No results found")
                else:
                    st.error(f"Error: {response.status_code} - {response.text}")
    elif search_button:
        st.warning("Please enter a search query")
    else:
        # Show welcome message when no search is performed
        with results_tab:
            st.markdown("""
                ### 👋 Welcome to Image Search!
                
                Start by typing your search query above. You can:
                - Search for similar images using natural language
                - Filter results by similarity score
                - Sort results by different criteria
                - View detailed image information
                
                Use the sidebar to customize your search experience.
            """)

if __name__ == "__main__":
    main() 