# Source Code Architecture

This document describes the architecture of the Image Search application's source code components and their interactions.

## Component Flow Diagram

```mermaid
graph TB
    subgraph "Image Processing Service"
        A[Image Upload] --> B[Cloud Function]
        B --> C[GeminiImageAnalyzer]
        B --> D[EmbeddingGenerator]
        B --> E[LocationService]
        
        C --> F[Image Analysis]
        D --> G[Vector Embedding]
        E --> H[Location Details]
        
        F --> I[VectorSearchClient]
        G --> I
        H --> I
        
        I --> J[(Vector Search Index)]
        I --> K[(Firestore Metadata)]
    end
    
    subgraph "Search API Service"
        L[Search Request] --> M[Flask API]
        M --> N[VectorSearchService]
        N --> O[MultiModalEmbedding]
        N --> P[(Vector Search Index)]
        N --> Q[(Firestore Metadata)]
        
        P --> R[Search Results]
        Q --> R
        R --> M
    end
    
    subgraph "UI Service"
        S[Streamlit UI] --> T[Search Form]
        T --> U[API Client]
        U --> M
        M --> U
        U --> V[Results Display]
        V --> W[Image Grid]
        V --> X[Metadata Cards]
    end

    style A fill:#f9f,stroke:#333
    style B fill:#bbf,stroke:#333
    style J fill:#bfb,stroke:#333
    style K fill:#bfb,stroke:#333
    style P fill:#bfb,stroke:#333
    style Q fill:#bfb,stroke:#333
    style S fill:#fbf,stroke:#333
```

## Component Description

### Image Processing Service

The Image Processing Service is responsible for analyzing and processing uploaded images. It consists of several key components:

1. **Cloud Function (`image_processor/main.py`)**
   - Triggered by image uploads to the raw images bucket
   - Orchestrates the image processing workflow

2. **GeminiImageAnalyzer (`image_processor/analyzer.py`)**
   - Uses Google's Gemini Vision model to analyze image content
   - Generates detailed descriptions and object annotations

3. **EmbeddingGenerator (`image_processor/embedding.py`)**
   - Creates vector embeddings from images using Vertex AI
   - Combines visual and textual features for search

4. **LocationService (`image_processor/location_service.py`)**
   - Extracts and validates location information
   - Integrates with Google Maps API for location details

5. **VectorSearchClient (`image_processor/vector_store.py`)**
   - Manages interactions with Vertex AI Vector Search
   - Stores embeddings and metadata in Firestore

### Search API Service

The Search API Service handles search requests and retrieves relevant images:

1. **Flask API (`search_api/main.py`)**
   - Provides RESTful endpoints for image search
   - Handles request validation and response formatting

2. **VectorSearchService (`search_api/vector_search.py`)**
   - Performs vector similarity search
   - Retrieves and combines results from Vector Search and Firestore

### UI Service

The UI Service provides the user interface for the application:

1. **Streamlit UI (`ui_search/app.py`)**
   - Responsive web interface for image search
   - Material Design-inspired components
   - Interactive image grid and metadata display

## Data Flow

1. **Image Upload Flow:**
   - Images are uploaded to the raw images bucket
   - Cloud Function processes the image:
     - Generates image analysis using Gemini
     - Creates vector embeddings
     - Extracts location information
     - Stores data in Vector Search and Firestore
   - Processed image is moved to the processed bucket

2. **Search Flow:**
   - User enters search query in UI
   - Query is sent to Flask API
   - API converts query to vector embedding
   - Vector Search finds similar images
   - Metadata is retrieved from Firestore
   - Results are displayed in UI grid

## Color Legend

- **Pink/Purple**: Entry points and UI components
- **Blue**: Processing and compute components
- **Green**: Storage and database components 