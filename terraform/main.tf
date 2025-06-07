terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Modules
module "bigquery" {
  source = "./modules/bigquery"

  project_id           = var.project_id
  dataset_id           = var.bigquery_dataset_id
  table_id             = var.bigquery_table_id
  location             = var.bigquery_location
  dataset_owner_email  = var.dataset_owner_email
  table_expiration_ms  = var.table_expiration_ms
  labels               = var.labels
}

module "iam" {
  source = "./modules/iam"

  project_id          = var.project_id
  cloud_run_sa_id     = var.cloud_run_sa_id
  pubsub_sa_id        = var.pubsub_sa_id
  bigquery_dataset_id = module.bigquery.dataset_id
  secret_id           = var.jquants_secret_id
  labels              = var.labels
}

module "cloud_run" {
  source = "./modules/cloud_run"

  project_id                    = var.project_id
  region                        = var.region
  service_name                  = var.cloud_run_service_name
  container_image               = var.container_image
  service_account_email         = module.iam.cloud_run_service_account_email
  pubsub_service_account_email  = module.iam.pubsub_service_account_email
  cpu_limit                     = var.cpu_limit
  memory_limit                  = var.memory_limit
  timeout_seconds               = var.timeout_seconds
  bigquery_dataset              = var.bigquery_dataset_id
  bigquery_table                = var.bigquery_table_id
  log_level                     = var.log_level
  jquants_secret_id             = var.jquants_secret_id
  labels                        = var.labels
}

module "scheduler" {
  source = "./modules/scheduler"

  topic_name                    = var.pubsub_topic_name
  subscription_name             = var.pubsub_subscription_name
  cloud_run_endpoint            = module.cloud_run.service_url
  pubsub_service_account_email  = module.iam.pubsub_service_account_email
  job_name                      = var.scheduler_job_name
  schedule                      = var.schedule
  labels                        = var.labels
}