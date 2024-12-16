# Create VPC network
resource "google_compute_network" "vertex_network" {
  name                    = "${var.index_name}-network"
  project = var.project_id
  auto_create_subnetworks = false
}

# Create global address for VPC peering
resource "google_compute_global_address" "vertex_range" {
  name          = "${var.index_name}-address-range"
  project = var.project_id
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vertex_network.id
}

# Create VPC peering connection
resource "google_service_networking_connection" "vertex_vpc_connection" {
  network                 = google_compute_network.vertex_network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.vertex_range.name]
}

# Vector Search Index
resource "google_vertex_ai_index" "image_search_index" {
  region       = var.region
  project = var.project_id
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

# Index Endpoint
resource "google_vertex_ai_index_endpoint" "image_search_endpoint" {
  region       = var.region
  project = var.project_id
  display_name = "${var.index_name}-endpoint"
  description  = "Vector search endpoint for image search index"
  
  network = "projects/${var.project_number}/global/networks/${google_compute_network.vertex_network.name}"
  
  depends_on = [
    google_service_networking_connection.vertex_vpc_connection
  ]
}

# Deploy Index to Endpoint
resource "google_vertex_ai_index_endpoint_deployed_index" "image_search_deployed_index" {
  depends_on = [
    google_vertex_ai_index_endpoint.image_search_endpoint
  ]

  index_endpoint   = google_vertex_ai_index_endpoint.image_search_endpoint.id
  deployed_index_id = "deployed_${replace(var.index_name, "-", "_")}"
  display_name     = "${var.index_name}-deployment"
  index            = google_vertex_ai_index.image_search_index.id
  
  reserved_ip_ranges = [google_compute_global_address.vertex_range.name]
  enable_access_logging = false

  dedicated_resources {
    machine_spec {
      machine_type = "e2-standard-2"
    }
    min_replica_count = 1
    max_replica_count = 2
  }

  deployed_index_auth_config {
    auth_provider {
      audiences = ["${var.project_id}"]
      allowed_issuers = [var.service_account_email]
    }
  }
}