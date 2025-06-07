terraform {
  backend "gcs" {
    # bucket = "terraform-state-{project-id}" will be configured during terraform init
    prefix = "stock-data-collector/prod"
  }
}