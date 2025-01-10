import streamlit as st
import requests
from typing import List, Dict
from mock_data import get_mock_results
import os
from dotenv import load_dotenv

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
    }

    .stImage:hover {
        transform: scale(1.02);
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
        padding: 4px 8px;
        border-radius: 16px;
        font-size: 0.85rem;
        margin-right: 4px;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

# Constants
API_ENDPOINT = os.getenv('API_ENDPOINT')
if not API_ENDPOINT:
    raise ValueError("API_ENDPOINT environment variable is not set")

def search_images(query: str, use_mock: bool = True) -> List[Dict]:
    """
    Search for images using either the real API or mock data
    """
    if use_mock:
        return get_mock_results(query)
    
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        response = requests.post(
            f"{API_ENDPOINT}/search",
            headers=headers,
            json={"query": query}
        )
        
        # Print response details for debugging
        st.write("Response Status:", response.status_code)
        st.write("Response Headers:", dict(response.headers))
        try:
            st.write("Response Body:", response.json())
        except:
            st.write("Response Text:", response.text)
            
        response.raise_for_status()
        return response.json().get('results', [])
    except requests.RequestException as e:
        st.error(f"Error connecting to API: {str(e)}")
        return []

def main():
    # Sidebar for settings
    with st.sidebar:
        st.title("⚙️ Settings")
        use_mock = st.toggle("Use mock data", value=True)
        st.divider()
        st.markdown("### Filters")
        min_similarity = st.slider("Minimum similarity", 0.0, 1.0, 0.5, 
                                 help="Filter results by minimum similarity score")
        sort_by = st.selectbox("Sort results by", 
                             ["Similarity", "Date", "Name"],
                             help="Choose how to sort the search results")
        st.divider()
        st.markdown("### About")
        st.markdown("""
            Image Search uses advanced AI to find similar images 
            in your collection based on visual features and content.
        """)
    
    # Main content
    st.title("🔍 Image Search")
    
    # Search container
    with st.container():
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input("", 
                                placeholder="Search images by description or content...", 
                                label_visibility="collapsed")
        with col2:
            search_button = st.button("Search", type="primary", use_container_width=True)
    
    # Handle search
    if search_button and query:
        with st.spinner("🔍 Searching for images..."):
            results = search_images(query, use_mock=use_mock)
            
            if results:
                # Filter results based on minimum similarity
                filtered_results = [r for r in results if r.get('similarity', 0) >= min_similarity]
                
                if not filtered_results:
                    st.warning("No results match your filter criteria.")
                    return
                
                # Sort results
                if sort_by == "Similarity":
                    filtered_results.sort(key=lambda x: x.get('similarity', 0), reverse=True)
                
                # Display results count with material design
                st.markdown(f"""
                    <div class="results-count">
                        📸 Found {len(filtered_results)} images
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                
                # Create grid layout
                cols = st.columns(3)
                for idx, result in enumerate(filtered_results):
                    with cols[idx % 3]:
                        with st.container():
                            # Image card with hover effect
                            st.image(
                                result.get("image_url", "placeholder.jpg"),
                                use_column_width=True
                            )
                            
                            # Similarity score
                            similarity = result.get('similarity', 0)
                            st.progress(similarity, text=f"Similarity: {similarity:.0%}")
                            
                            # Metadata expansion
                            with st.expander("Details"):
                                if 'metadata' in result:
                                    st.markdown("**Description**")
                                    st.write(result['metadata'].get('description', 'N/A'))
                                    
                                    st.markdown("**Tags**")
                                    tags_html = " ".join([
                                        f'<span class="tag">{tag}</span>' 
                                        for tag in result['metadata'].get('tags', [])
                                    ])
                                    st.markdown(tags_html, unsafe_allow_html=True)
                                    
                                    st.markdown("**Properties**")
                                    col1, col2 = st.columns(2)
                                    with col1:
                                        st.write("Size:", result['metadata'].get('size', 'N/A'))
                                    with col2:
                                        st.write("Added:", result['metadata'].get('date_added', 'N/A'))
            else:
                st.warning("No results found")
    elif search_button:
        st.warning("Please enter a search query")
    else:
        # Show welcome message when no search is performed
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