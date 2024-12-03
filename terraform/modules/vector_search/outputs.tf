output "network_id" {
  value       = google_compute_network.vertex_network.id
  description = "The ID of the created VPC network"
}

output "index_endpoint_id" {
  value       = google_vertex_ai_index_endpoint.image_search_endpoint.id
  description = "The ID of the created index endpoint"
}

output "deployed_index_id" {
  value       = google_vertex_ai_index_endpoint_deployed_index.image_search_deployed_index.id
  description = "The ID of the deployed index"
}

output "endpoint_network" {
  value       = google_vertex_ai_index_endpoint.image_search_endpoint.network
  description = "The network where the endpoint is deployed"
}