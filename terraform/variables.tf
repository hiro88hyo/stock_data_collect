variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "asia-northeast1"
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

# BigQuery
variable "bigquery_dataset_id" {
  description = "BigQuery dataset ID"
  type        = string
}

variable "bigquery_table_id" {
  description = "BigQuery table ID"
  type        = string
  default     = "daily_stock_prices"
}

variable "bigquery_location" {
  description = "BigQuery dataset location"
  type        = string
  default     = "asia-northeast1"
}

variable "dataset_owner_email" {
  description = "Email of the dataset owner"
  type        = string
}

variable "table_expiration_ms" {
  description = "Default table expiration in milliseconds"
  type        = number
  default     = null
}

# Cloud Run
variable "cloud_run_service_name" {
  description = "Cloud Run service name"
  type        = string
}

variable "container_image" {
  description = "Container image URL"
  type        = string
}

variable "cloud_run_sa_id" {
  description = "Cloud Run service account ID"
  type        = string
  default     = "stock-data-collector-sa"
}

variable "cpu_limit" {
  description = "CPU limit for Cloud Run"
  type        = string
  default     = "1"
}

variable "memory_limit" {
  description = "Memory limit for Cloud Run"
  type        = string
  default     = "1Gi"
}

variable "timeout_seconds" {
  description = "Timeout for Cloud Run in seconds"
  type        = number
  default     = 1800
}

variable "log_level" {
  description = "Log level for the application"
  type        = string
  default     = "INFO"
}

# Pub/Sub
variable "pubsub_topic_name" {
  description = "Pub/Sub topic name"
  type        = string
  default     = "stock-data-trigger"
}

variable "pubsub_subscription_name" {
  description = "Pub/Sub subscription name"
  type        = string
  default     = "stock-data-processor"
}

variable "pubsub_sa_id" {
  description = "Pub/Sub service account ID"
  type        = string
  default     = "stock-data-pubsub-sa"
}

# Cloud Scheduler
variable "scheduler_job_name" {
  description = "Cloud Scheduler job name"
  type        = string
  default     = "daily-stock-data"
}

variable "schedule" {
  description = "Cron schedule for Cloud Scheduler"
  type        = string
  default     = "30 16 * * 1-5"
}

# Secret Manager
variable "jquants_secret_id" {
  description = "Secret ID for J-Quants refresh token"
  type        = string
  default     = "jquants-refresh-token"
}

# Labels
variable "labels" {
  description = "Labels to apply to all resources"
  type        = map(string)
  default     = {
    managed_by = "terraform"
    project    = "stock-data-collector"
  }
}