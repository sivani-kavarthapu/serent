# Clinical BERT Real-Time Inference API

A production-ready FastAPI service for clinical text classification using the Hugging Face `bvanaken/clinical-assertion-negation-bert` model. This API classifies clinical sentences into assertion status categories: **PRESENT**, **ABSENT**, or **CONDITIONAL**.

## 🎯 Features

- **FastAPI-based REST API** with automatic OpenAPI documentation
- **Model caching**: Model loads once at startup for optimal performance
- **Single & batch predictions**: Support for both individual and batch sentence processing
- **Health check endpoint**: Monitor service status and model loading
- **Production-ready**: Dockerized, tested, and CI/CD enabled
- **Performance**: Optimized for <500ms response time
- **Cloud deployment**: Ready for Google Cloud Run deployment

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Setup Instructions](#setup-instructions)
- [Local Development](#local-development)
- [API Usage](#api-usage)
- [Testing](#testing)
- [Deployment](#deployment)
- [Known Issues & Tradeoffs](#known-issues--tradeoffs)

## 📖 Project Overview

This API uses the `bvanaken/clinical-assertion-negation-bert` model from Hugging Face to classify clinical sentences. The model predicts assertion status:

- **PRESENT**: Medical concept is present/affirmed
- **ABSENT**: Medical concept is absent/denied
- **CONDITIONAL**: Medical concept is conditional/hypothetical

### Model Information

- **Model**: [bvanaken/clinical-assertion-negation-bert](https://huggingface.co/bvanaken/clinical-assertion-negation-bert)
- **Task**: Clinical assertion/negation classification
- **Input**: Clinical sentences
- **Output**: Label (PRESENT/ABSENT/CONDITIONAL) and confidence score

## 🚀 Setup Instructions

### Prerequisites

- Python 3.12+
- Docker (for containerized deployment)
- Google Cloud SDK (for GCP deployment, optional)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd clinical-bert-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8080
   ```

   Or use Python directly:
   ```bash
   python -m app.main
   ```

5. **Access the API**
   - API: http://localhost:8080
   - Interactive docs: http://localhost:8080/docs
   - Health check: http://localhost:8080/health

## 💻 Local Development

### Project Structure

```
clinical-bert-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application
│   ├── model.py         # Model loading & prediction logic
│   └── schemas.py       # Pydantic schemas for validation
├── tests/
│   ├── __init__.py
│   └── test_api.py      # Test cases
├── .github/
│   └── workflows/
│       ├── ci.yml       # CI workflow
│       └── cd.yml       # CD workflow
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── pyproject.toml
├── deploy.sh            # GCP deployment script
└── README.md
```

### Code Formatting

This project uses `black`, `isort`, and `flake8` for code quality:

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/
```

## 📡 API Usage

### Endpoints

#### 1. Root Endpoint
```bash
GET /
```

#### 2. Health Check
```bash
GET /health
```

Response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "version": "1.0.0"
}
```

#### 3. Single Prediction
```bash
POST /predict
```

Request:
```json
{
  "sentence": "The patient denies chest pain."
}
```

Response:
```json
{
  "label": "ABSENT",
  "score": 0.9842
}
```

#### 4. Batch Prediction
```bash
POST /predict/batch
```

Request:
```json
{
  "sentences": [
    "The patient denies chest pain.",
    "He has a history of hypertension.",
    "If the patient experiences dizziness, reduce the dosage."
  ]
}
```

Response:
```json
{
  "predictions": [
    {"label": "ABSENT", "score": 0.9842},
    {"label": "PRESENT", "score": 0.9234},
    {"label": "CONDITIONAL", "score": 0.8765}
  ]
}
```

### Python Example

```python
import requests

# Single prediction
response = requests.post(
    "http://localhost:8080/predict",
    json={"sentence": "The patient denies chest pain."}
)
print(response.json())
# Output: {"label": "ABSENT", "score": 0.9842}

# Batch prediction
response = requests.post(
    "http://localhost:8080/predict/batch",
    json={
        "sentences": [
            "The patient denies chest pain.",
            "He has a history of hypertension."
        ]
    }
)
print(response.json())
```

### cURL Examples

```bash
# Health check
curl http://localhost:8080/health

# Single prediction
curl -X POST http://localhost:8080/predict \
  -H "Content-Type: application/json" \
  -d '{"sentence": "The patient denies chest pain."}'

# Batch prediction
curl -X POST http://localhost:8080/predict/batch \
  -H "Content-Type: application/json" \
  -d '{"sentences": ["The patient denies chest pain.", "He has a history of hypertension."]}'
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_api.py::test_predict_absent
```

### Test Cases

The test suite includes:
- ✅ Root endpoint test
- ✅ Health check test
- ✅ Single prediction tests (all expected labels)
- ✅ Batch prediction tests
- ✅ Input validation tests
- ✅ Response time tests

## ☁️ Deployment

### Google Cloud Run Deployment

#### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **Google Cloud SDK** installed and configured
3. **Docker** installed and running

#### Step-by-Step Deployment

##### 1. Set Up Google Cloud Project

```bash
# Install Google Cloud SDK (if not installed)
# macOS: brew install google-cloud-sdk
# Linux: Follow https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login

# Create a new project (or use existing)
gcloud projects create your-project-id --name="Clinical BERT API"

# Set the project
gcloud config set project your-project-id

# Enable billing (required for Cloud Run)
# Do this via the GCP Console: https://console.cloud.google.com/billing
```

##### 2. Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

##### 3. Create Artifact Registry Repository

```bash
gcloud artifacts repositories create clinical-bert-api \
    --repository-format=docker \
    --location=us-central1 \
    --description="Docker repository for Clinical BERT API"
```

##### 4. Configure Docker Authentication

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

##### 5. Build and Push Docker Image

**Option A: Using the deployment script**

```bash
# Set environment variables
export GCP_PROJECT_ID=your-project-id
export GAR_LOCATION=us-central1
export GCP_REGION=us-central1

# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

**Option B: Manual deployment**

```bash
# Set variables
PROJECT_ID=your-project-id
GAR_LOCATION=us-central1
SERVICE_NAME=clinical-bert-api
REGION=us-central1
IMAGE_NAME=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/clinical-bert-api

# Build image
docker build -t $IMAGE_NAME:latest .

# Push to Artifact Registry
docker push $IMAGE_NAME:latest

# Deploy to Cloud Run
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
```

##### 6. Get Service URL

```bash
gcloud run services describe clinical-bert-api \
    --region us-central1 \
    --format 'value(status.url)'
```

##### 7. Test Deployment

```bash
# Replace with your actual URL
SERVICE_URL=https://clinical-bert-api-xxxxx.run.app

# Health check
curl $SERVICE_URL/health

# Test prediction
curl -X POST $SERVICE_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"sentence": "The patient denies chest pain."}'
```

### CI/CD with GitHub Actions

The project includes GitHub Actions workflows for automated CI/CD.

#### Setup GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions, and add:

1. **GCP_PROJECT_ID**: Your Google Cloud project ID
2. **GAR_LOCATION**: Artifact Registry location (e.g., `us-central1`)
3. **GCP_REGION**: Cloud Run region (e.g., `us-central1`)
4. **GCP_SA_KEY**: Service account key JSON (see below)

#### Create Service Account

```bash
# Create service account
gcloud iam service-accounts create github-actions \
    --display-name="GitHub Actions Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-actions@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"

# Create and download key
gcloud iam service-accounts keys create key.json \
    --iam-account=github-actions@$PROJECT_ID.iam.gserviceaccount.com

# Copy the contents of key.json to GitHub secret GCP_SA_KEY
```

#### Workflows

- **CI** (`ci.yml`): Runs on PRs and pushes to main
  - Linting (black, isort, flake8)
  - Unit tests
  - Coverage reporting

- **CD** (`cd.yml`): Runs on pushes to main
  - Builds Docker image
  - Pushes to Artifact Registry
  - Deploys to Cloud Run

### Docker Deployment (Local/Other Platforms)

```bash
# Build image
docker build -t serent.

# Run container
docker run -p 8080:8080 serent

# Test
curl http://localhost:8080/health
```

## ⚠️ Known Issues & Tradeoffs

### Performance Considerations

1. **Cold Start**: First request may take longer due to model loading (~10-30 seconds)
   - **Mitigation**: Use Cloud Run with `min-instances=1` to keep a warm instance
   - **Tradeoff**: Higher cost due to always-on instance

2. **Memory Usage**: Model requires ~500MB-1GB RAM
   - **Mitigation**: Cloud Run configured with 2Gi memory
   - **Tradeoff**: Higher memory = higher cost

3. **Response Time**: Target <500ms achieved after warmup
   - First request: ~2-5 seconds (model warmup)
   - Subsequent requests: ~100-400ms

### Model Limitations

1. **Input Length**: Maximum 512 tokens (handled via truncation)
2. **Domain**: Optimized for clinical text; may not perform well on general text
3. **Language**: English only

### Cost Considerations (GCP Free Tier)

- **Free Tier**: $300 credit for new users (90 days)
- **Cloud Run**: Free tier includes 2 million requests/month
- **Artifact Registry**: First 0.5 GB storage free
- **Estimated Cost**: ~$0.10-0.50/month for low traffic (<1000 requests/day)

### Security Considerations

1. **CORS**: Currently allows all origins (`allow_origins=["*"]`)
   - **Production**: Restrict to specific domains
2. **Authentication**: Cloud Run allows unauthenticated access
   - **Production**: Enable authentication or use API keys
3. **Rate Limiting**: Not implemented
   - **Production**: Add rate limiting middleware

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers)
- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Model Card](https://huggingface.co/bvanaken/clinical-assertion-negation-bert)

## 📝 License

This project is provided as-is for the take-home assignment.

## 🤝 Contributing

This is a take-home assignment project. For production use, consider:
- Adding authentication/authorization
- Implementing rate limiting
- Adding monitoring and logging (e.g., Cloud Monitoring)
- Setting up alerting
- Adding more comprehensive error handling
- Implementing request/response caching for common queries

