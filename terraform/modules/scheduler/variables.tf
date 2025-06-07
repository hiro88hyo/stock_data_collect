variable "topic_name" {
  description = "Pub/Sub topic name"
  type        = string
}

variable "subscription_name" {
  description = "Pub/Sub subscription name"
  type        = string
}

variable "cloud_run_endpoint" {
  description = "Cloud Run service endpoint URL"
  type        = string
}

variable "pubsub_service_account_email" {
  description = "Service account email for Pub/Sub"
  type        = string
}

variable "job_name" {
  description = "Cloud Scheduler job name"
  type        = string
}

variable "schedule" {
  description = "Cron schedule for Cloud Scheduler"
  type        = string
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}