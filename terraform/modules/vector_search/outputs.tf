output "index_endpoint_id" {
  value       = google_vertex_ai_index_endpoint.image_search_endpoint.id
  description = "The ID of the created index endpoint"
}

output "deployed_index_id" {
  value       = google_vertex_ai_index_endpoint_deployed_index.image_search_deployed_index.id
  description = "The ID of the deployed index"
}


output "index_id" {
  value       = google_vertex_ai_index.image_search_index.id
  description = "Vector Search Index ID"
}