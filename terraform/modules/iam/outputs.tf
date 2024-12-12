output "service_account_email" {
  value       = google_service_account.vertex_sa.email
  description = "Service Account email"
}

output "eventarc_service_agent" {
  value = google_project_iam_member.eventarc_service_agent
}