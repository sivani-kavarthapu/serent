# Quick Start Guide

Get the Clinical BERT API running in 5 minutes!

## Local Development

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 3. Test It

```bash
# Health check
curl http://localhost:8000/health

# Make a prediction
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"sentence": "The patient denies chest pain."}'
```

### 4. View API Docs

Open http://localhost:8000/docs in your browser

## Docker (Local)

```bash
# Build
docker build -t clinical-bert-api .

# Run
docker run -p 8000:8000 clinical-bert-api

# Test
curl http://localhost:8000/health
```

## Deploy to Google Cloud Run

### Prerequisites

1. Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
2. Install [Docker](https://www.docker.com/get-started)
3. Create a [Google Cloud Project](https://console.cloud.google.com/)

### Quick Deploy

```bash
# 1. Authenticate
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# 2. Enable APIs
gcloud services enable cloudbuild.googleapis.com run.googleapis.com artifactregistry.googleapis.com

# 3. Deploy (using script)
export GCP_PROJECT_ID=your-project-id
export GAR_LOCATION=us-central1
export GCP_REGION=us-central1
./deploy.sh
```

### Manual Deploy

```bash
PROJECT_ID=$(gcloud config get-value project)
GAR_LOCATION=us-central1
IMAGE_NAME=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/clinical-bert-api/clinical-bert-api

# Build and push
docker build -t $IMAGE_NAME:latest .
gcloud auth configure-docker $GAR_LOCATION-docker.pkg.dev
docker push $IMAGE_NAME:latest

# Deploy
gcloud run deploy clinical-bert-api \
    --image $IMAGE_NAME:latest \
    --region us-central1 \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2
```

## Run Tests

```bash
# Install test dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html
```

## Next Steps

- Read [README.md](README.md) for detailed documentation
- Read [DEPLOYMENT.md](DEPLOYMENT.md) for comprehensive deployment guide
- Check API docs at http://localhost:8000/docs

