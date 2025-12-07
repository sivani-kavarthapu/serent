#!/bin/bash
# Deployment script for Google Cloud Run

set -e

# Configuration (update these values)
PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
GAR_LOCATION="${GAR_LOCATION:-us-central1}"
SERVICE_NAME="serent"
REGION="${GCP_REGION:-us-central1}"
IMAGE_NAME="$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/serent"

echo "🚀 Starting deployment to Google Cloud Run..."

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Set the project
echo "📋 Setting GCP project to $PROJECT_ID..."
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com

# Create Artifact Registry repository if it doesn't exist
echo "📦 Creating Artifact Registry repository..."
gcloud artifacts repositories create $SERVICE_NAME \
    --repository-format=docker \
    --location=$GAR_LOCATION \
    --description="Docker repository for Clinical BERT API" \
    2>/dev/null || echo "Repository already exists, skipping..."

# Configure Docker authentication
echo "🔐 Configuring Docker authentication..."
gcloud auth configure-docker $GAR_LOCATION-docker.pkg.dev

# Build Docker image
echo "🏗️  Building Docker image..."
docker build -t $IMAGE_NAME:latest .

# Push image to Artifact Registry
echo "📤 Pushing image to Artifact Registry..."
docker push $IMAGE_NAME:latest

# Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --min-instances 0 \
    --port 8080

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')

echo ""
echo "✅ Deployment successful!"
echo "📍 Service URL: $SERVICE_URL"
echo "🔍 Health check: $SERVICE_URL/health"
echo "📚 API docs: $SERVICE_URL/docs"

