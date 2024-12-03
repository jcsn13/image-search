output "service_account_email" {
  value       = google_service_account.vertex_sa.email
  description = "Service Account email"
}