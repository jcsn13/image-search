output "function_name" {
  description = "The name of the deployed function"
  value       = google_cloudfunctions2_function.image_processor.name
}

output "function_uri" {
  description = "The URI of the deployed function"
  value       = google_cloudfunctions2_function.image_processor.service_config[0].uri
}