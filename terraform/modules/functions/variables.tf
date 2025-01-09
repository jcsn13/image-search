variable "project_id" {
  description = "The ID of the project"
  type        = string
}

variable "region" {
  description = "The region for resources"
  type        = string
  default     = "us-central1"
}

variable "project_number" {
  description = "The number of the project"
  type        = string
}

variable "raw_bucket_name" {
  description = "Name of the bucket containing raw images"
  type        = string
}

variable "processed_bucket_name" {
  description = "Name of the bucket for processed images"
  type        = string
}

variable "vector_search_index_id" {
  description = "ID of the Vertex AI Vector Search index"
  type        = string
}

variable "memory" {
  description = "Memory allocated to the function"
  type        = string
  default     = "2048Mi"
}

variable "timeout_seconds" {
  description = "Function timeout in seconds"
  type        = number
  default     = 540
}

variable "min_instances" {
  description = "Minimum number of instances"
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "Maximum number of instances"
  type        = number
  default     = 10
}

variable "service_account_email" {
  description = "Service Account email for cloud function"
  type = string
}

variable "maps_api_key_secret_id" {
  type = string
  description = "Secret ID for the Google Maps API key"
}