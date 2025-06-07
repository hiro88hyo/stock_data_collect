resource "google_cloud_run_v2_service" "stock_data_collector" {
  name     = var.service_name
  location = var.region

  template {
    service_account = var.service_account_email
    
    containers {
      image = var.container_image
      
      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "BIGQUERY_DATASET"
        value = var.bigquery_dataset
      }

      env {
        name  = "BIGQUERY_TABLE"
        value = var.bigquery_table
      }

      env {
        name  = "BIGQUERY_LOCATION"
        value = var.region
      }

      env {
        name  = "LOG_LEVEL"
        value = var.log_level
      }

      env {
        name  = "JQUANTS_BASE_URL"
        value = "https://api.jquants.com"
      }

      env {
        name  = "JQUANTS_REFRESH_TOKEN_SECRET"
        value = var.jquants_secret_id
      }

      env {
        name  = "RETRY_MAX_ATTEMPTS"
        value = "3"
      }

      env {
        name  = "TIMEOUT_SECONDS"
        value = "30"
      }

      env {
        name  = "PORT"
        value = "8080"
      }

      ports {
        container_port = 8080
      }

      startup_probe {
        initial_delay_seconds = 0
        timeout_seconds       = 1
        period_seconds        = 3
        failure_threshold     = 1
        tcp_socket {
          port = 8080
        }
      }

      liveness_probe {
        initial_delay_seconds = 10
        timeout_seconds       = 1
        period_seconds        = 10
        failure_threshold     = 3
        http_get {
          path = "/health"
          port = 8080
        }
      }
    }

    timeout = "${var.timeout_seconds}s"
    
    scaling {
      max_instance_count = 1
      min_instance_count = 0
    }
  }

  labels = var.labels
}

resource "google_cloud_run_service_iam_member" "pubsub_invoker" {
  location = google_cloud_run_v2_service.stock_data_collector.location
  service  = google_cloud_run_v2_service.stock_data_collector.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${var.pubsub_service_account_email}"
}