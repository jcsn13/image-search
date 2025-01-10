# Vector Search Index
resource "google_vertex_ai_index" "image_search_index" {
  region       = var.region
  project      = var.project_id
  display_name = var.index_name
  description  = "Vector search index for image search"
  
  metadata {
    contents_delta_uri = "gs://${var.project_id}-processed-images"
    config {
      dimensions = var.dimensions            
      approximate_neighbors_count = 150 
      distance_measure_type = "DOT_PRODUCT_DISTANCE"
      shard_size = "SHARD_SIZE_SMALL"
      algorithm_config {
        tree_ah_config {
          leaf_node_embedding_count = 500 
          leaf_nodes_to_search_percent = 10
        }
      }
    }
  }

  index_update_method = "STREAM_UPDATE"
}

# Index Endpoint with public access
resource "google_vertex_ai_index_endpoint" "image_search_endpoint" {
  region       = var.region
  project      = var.project_id
  display_name = "${var.index_name}-endpoint"
  description  = "Vector search endpoint for image search index"
  
  public_endpoint_enabled = true  # Enable public endpoint
}

# Deploy Index to Endpoint
resource "google_vertex_ai_index_endpoint_deployed_index" "image_search_deployed_index" {
  index_endpoint   = google_vertex_ai_index_endpoint.image_search_endpoint.id
  deployed_index_id = "deployed_${replace(var.index_name, "-", "_")}"
  display_name     = "${var.index_name}-deployment"
  index            = google_vertex_ai_index.image_search_index.id
  
  enable_access_logging = false

  dedicated_resources {
    machine_spec {
      machine_type = "e2-standard-2"
    }
    min_replica_count = 1
    max_replica_count = 2
  }
}