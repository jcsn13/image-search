output "api_endpoint" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.search_api_app.uri
}