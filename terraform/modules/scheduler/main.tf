resource "google_pubsub_topic" "stock_data_trigger" {
  name = var.topic_name

  labels = var.labels
}

resource "google_pubsub_subscription" "stock_data_processor" {
  name  = var.subscription_name
  topic = google_pubsub_topic.stock_data_trigger.name

  ack_deadline_seconds       = 600
  message_retention_duration = "604800s" # 7 days

  push_config {
    push_endpoint = var.cloud_run_endpoint
    
    oidc_token {
      service_account_email = var.pubsub_service_account_email
    }
  }

  retry_policy {
    minimum_backoff = "10s"
    maximum_backoff = "600s"
  }

  expiration_policy {
    ttl = ""
  }

  labels = var.labels
}

resource "google_cloud_scheduler_job" "daily_stock_data" {
  name        = var.job_name
  description = "Daily stock data collection trigger"
  schedule    = var.schedule
  time_zone   = "Asia/Tokyo"

  pubsub_target {
    topic_name = google_pubsub_topic.stock_data_trigger.id
    data       = base64encode(jsonencode({
      trigger_type = "daily"
      date         = ""
    }))
  }

  retry_config {
    retry_count = 1
  }

  labels = var.labels
}