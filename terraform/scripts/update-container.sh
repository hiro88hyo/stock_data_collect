#!/bin/bash
# Update Cloud Run service with new container image

set -e

ENVIRONMENT=${1:-dev}
PROJECT_ID=${2}
IMAGE_TAG=${3:-latest}

if [ -z "$PROJECT_ID" ]; then
  echo "Usage: $0 <environment> <project_id> [image_tag]"
  echo "Example: $0 dev my-project-id v1.0.0"
  exit 1
fi

# Set service name based on environment
if [ "$ENVIRONMENT" = "prod" ]; then
  SERVICE_NAME="stock-data-collector"
else
  SERVICE_NAME="stock-data-collector-$ENVIRONMENT"
fi

IMAGE_URL="gcr.io/$PROJECT_ID/stock-data-collector:$IMAGE_TAG"

echo "===================="
echo "Updating Cloud Run service"
echo "Environment: $ENVIRONMENT"
echo "Project ID: $PROJECT_ID"
echo "Service Name: $SERVICE_NAME"
echo "Image: $IMAGE_URL"
echo "===================="

# Update Cloud Run service
echo "Updating Cloud Run service with new image..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_URL \
  --region asia-northeast1 \
  --project $PROJECT_ID \
  --no-allow-unauthenticated

echo ""
echo "===================="
echo "Update completed successfully!"
echo "===================="
echo ""
echo "To check the deployment status:"
echo "  gcloud run services describe $SERVICE_NAME --region asia-northeast1 --project $PROJECT_ID"
echo ""
echo "To view logs:"
echo "  gcloud logging read \"resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICE_NAME\" --project $PROJECT_ID --limit 50"