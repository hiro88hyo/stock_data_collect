resource "google_bigquery_dataset" "stock_data" {
  dataset_id                  = var.dataset_id
  friendly_name               = "Stock Data Dataset"
  description                 = "Dataset for Japanese stock market data"
  location                    = var.location
  default_table_expiration_ms = var.table_expiration_ms

  labels = var.labels

  access {
    role          = "OWNER"
    user_by_email = var.dataset_owner_email
  }

  access {
    role          = "WRITER"
    special_group = "projectWriters"
  }

  access {
    role          = "READER"
    special_group = "projectReaders"
  }
}

resource "google_bigquery_table" "daily_stock_prices" {
  dataset_id = google_bigquery_dataset.stock_data.dataset_id
  table_id   = var.table_id

  description = "Daily stock prices for Japanese market"
  labels      = var.labels

  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  clustering = ["security_code"]

  schema = jsonencode([
    {
      name        = "date"
      type        = "DATE"
      mode        = "REQUIRED"
      description = "Trading date"
    },
    {
      name        = "security_code"
      type        = "STRING"
      mode        = "REQUIRED"
      description = "Security code"
    },
    {
      name        = "security_name"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Security name"
    },
    {
      name        = "market_code"
      type        = "STRING"
      mode        = "NULLABLE"
      description = "Market code"
    },
    {
      name        = "open_price"
      type        = "NUMERIC"
      mode        = "NULLABLE"
      description = "Opening price"
    },
    {
      name        = "high_price"
      type        = "NUMERIC"
      mode        = "NULLABLE"
      description = "Highest price"
    },
    {
      name        = "low_price"
      type        = "NUMERIC"
      mode        = "NULLABLE"
      description = "Lowest price"
    },
    {
      name        = "close_price"
      type        = "NUMERIC"
      mode        = "NULLABLE"
      description = "Closing price"
    },
    {
      name        = "volume"
      type        = "INTEGER"
      mode        = "NULLABLE"
      description = "Trading volume"
    },
    {
      name        = "turnover_value"
      type        = "NUMERIC"
      mode        = "NULLABLE"
      description = "Turnover value"
    },
    {
      name        = "created_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Record creation timestamp"
      default_value_expression = "CURRENT_TIMESTAMP()"
    },
    {
      name        = "updated_at"
      type        = "TIMESTAMP"
      mode        = "REQUIRED"
      description = "Record update timestamp"
      default_value_expression = "CURRENT_TIMESTAMP()"
    }
  ])
}