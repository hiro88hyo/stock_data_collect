variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "cloud_run_sa_id" {
  description = "Cloud Run service account ID"
  type        = string
}

variable "pubsub_sa_id" {
  description = "Pub/Sub service account ID"
  type        = string
}

variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "secret_id" {
  description = "Secret ID for J-Quants refresh token"
  type        = string
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}