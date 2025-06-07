variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "service_account_email" {
  description = "Service account email for Cloud Run"
  type        = string
}

variable "pubsub_service_account_email" {
  description = "Service account email for Pub/Sub"
  type        = string
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run"
  type        = string
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run"
  type        = string
}

variable "timeout_seconds" {
  description = "Timeout for Cloud Run in seconds"
  type        = number
}

variable "bigquery_dataset" {
  description = "BigQuery dataset name"
  type        = string
}

variable "bigquery_table" {
  description = "BigQuery table name"
  type        = string
}

variable "log_level" {
  description = "Log level for the application"
  type        = string
}

variable "jquants_secret_id" {
  description = "Secret ID for J-Quants refresh token"
  type        = string
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}