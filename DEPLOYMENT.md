# Detailed Deployment Guide

This document provides step-by-step instructions for deploying the Clinical BERT API to Google Cloud Run.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Manual Deployment](#manual-deployment)
4. [Automated Deployment](#automated-deployment)
5. [CI/CD Setup](#cicd-setup)
6. [Post-Deployment](#post-deployment)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

### Required Software

1. **Google Cloud SDK (gcloud)**
   ```bash
   # macOS
   brew install google-cloud-sdk
   
   # Linux
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Windows
   # Download from https://cloud.google.com/sdk/docs/install
   ```

2. **Docker**
   ```bash
   # macOS/Windows: Download Docker Desktop
   # Linux
   sudo apt-get update
   sudo apt-get install docker.io
   ```

3. **Python 3.12+** (for local testing)
   ```bash
   python --version  # Should be 3.12+
   ```

### Google Cloud Account Setup

1. **Create Google Cloud Account**
   - Go to https://cloud.google.com/
   - Sign up (new users get $300 free credit)

2. **Create a Project**
   ```bash
   gcloud projects create clinical-bert-api-project \
       --name="Clinical BERT API" \
       --set-as-default
   ```

   Or via Console: https://console.cloud.google.com/projectcreate

3. **Enable Billing**
   - Go to https://console.cloud.google.com/billing
   - Link a billing account (required for Cloud Run)
   - Free tier includes generous limits

## Initial Setup

### 1. Authenticate with Google Cloud

```bash
# Login to Google Cloud
gcloud auth login

# Set default project
gcloud config set project YOUR_PROJECT_ID

# Verify
gcloud config list
```

### 2. Enable Required APIs

```bash
PROJECT_ID=$(gcloud config get-value project)

gcloud services enable cloudbuild.googleapis.com \
    --project=$PROJECT_ID

gcloud services enable run.googleapis.com \
    --project=$PROJECT_ID

gcloud services enable artifactregistry.googleapis.com \
    --project=$PROJECT_ID

# Verify APIs are enabled
gcloud services list --enabled
```

### 3. Create Artifact Registry Repository

```bash
PROJECT_ID=$(gcloud config get-value project)
GAR_LOCATION=us-central1
REPO_NAME=clinical-bert-api

gcloud artifacts repositories create $REPO_NAME \
    --repository-format=docker \
    --location=$GAR_LOCATION \
    --description="Docker repository for Clinical BERT API" \
    --project=$PROJECT_ID
```

### 4. Configure Docker Authentication

```bash
GAR_LOCATION=us-central1
gcloud auth configure-docker $GAR_LOCATION-docker.pkg.dev
```

## Manual Deployment

### Step 1: Build Docker Image Locally

```bash
# Set variables
PROJECT_ID=$(gcloud config get-value project)
GAR_LOCATION=us-central1
SERVICE_NAME=clinical-bert-api
IMAGE_NAME=$GAR_LOCATION-docker.pkg.dev/$PROJECT_ID/$SERVICE_NAME/clinical-bert-api

# Build image
docker build -t $IMAGE_NAME:latest .

# Test locally (optional)
docker run -p 8000:8000 $IMAGE_NAME:latest
# In another terminal: curl http://localhost:8000/health
```

### Step 2: Push Image to Artifact Registry

```bash
# Push image
docker push $IMAGE_NAME:latest

# Verify image exists
gcloud artifacts docker images list $IMAGE_NAME
```

### Step 3: Deploy to Cloud Run

```bash
REGION=us-central1

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
    --port 8000 \
    --project $PROJECT_ID
```

**Configuration Explanation:**
- `--memory 2Gi`: Model requires ~1GB, 2Gi provides buffer
- `--cpu 2`: Better performance for inference
- `--timeout 300`: 5 minutes max request time
- `--max-instances 10`: Scale up to 10 instances
- `--min-instances 0`: Scale to zero when idle (cost optimization)
- `--allow-unauthenticated`: Public access (change for production)

### Step 4: Get Service URL

```bash
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format 'value(status.url)')

echo "Service URL: $SERVICE_URL"
```

### Step 5: Test Deployment

```bash
# Health check
curl $SERVICE_URL/health

# Test prediction
curl -X POST $SERVICE_URL/predict \
  -H "Content-Type: application/json" \
  -d '{"sentence": "The patient denies chest pain."}'

# Expected response:
# {"label":"ABSENT","score":0.9842}
```

## Automated Deployment

### Using the Deployment Script

1. **Set Environment Variables**

   ```bash
   export GCP_PROJECT_ID=your-project-id
   export GAR_LOCATION=us-central1
   export GCP_REGION=us-central1
   ```

2. **Run Deployment Script**

   ```bash
   ./deploy.sh
   ```

   The script will:
   - Check prerequisites
   - Enable required APIs
   - Create Artifact Registry repository
   - Build Docker image
   - Push to Artifact Registry
   - Deploy to Cloud Run
   - Output service URL

### Using Cloud Build (Alternative)

```bash
# Create cloudbuild.yaml
cat > cloudbuild.yaml << EOF
steps:
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/clinical-bert-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/clinical-bert-api']
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'clinical-bert-api'
      - '--image'
      - 'gcr.io/$PROJECT_ID/clinical-bert-api'
      - '--region'
      - 'us-central1'
      - '--platform'
      - 'managed'
      - '--allow-unauthenticated'
images:
  - 'gcr.io/$PROJECT_ID/clinical-bert-api'
EOF

# Submit build
gcloud builds submit --config cloudbuild.yaml
```

## CI/CD Setup

### GitHub Actions Configuration

#### 1. Create Service Account

```bash
PROJECT_ID=$(gcloud config get-value project)
SA_NAME=github-actions
SA_EMAIL=$SA_NAME@$PROJECT_ID.iam.gserviceaccount.com

# Create service account
gcloud iam service-accounts create $SA_NAME \
    --display-name="GitHub Actions Service Account" \
    --project=$PROJECT_ID

# Grant permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/run.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/iam.serviceAccountUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA_EMAIL" \
    --role="roles/storage.admin"
```

#### 2. Create and Download Service Account Key

```bash
# Create key
gcloud iam service-accounts keys create key.json \
    --iam-account=$SA_EMAIL

# Display key (copy this)
cat key.json

# Clean up local key file
rm key.json
```

#### 3. Configure GitHub Secrets

Go to your GitHub repository:
1. Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add the following secrets:

   - **GCP_PROJECT_ID**: Your GCP project ID
   - **GAR_LOCATION**: `us-central1` (or your preferred location)
   - **GCP_REGION**: `us-central1` (or your preferred region)
   - **GCP_SA_KEY**: Paste the entire contents of `key.json`

#### 4. Push to Main Branch

```bash
git add .
git commit -m "Add CI/CD workflows"
git push origin main
```

The CD workflow will automatically:
- Build Docker image
- Push to Artifact Registry
- Deploy to Cloud Run

## Post-Deployment

### 1. Monitor Service

```bash
# View logs
gcloud run services logs read $SERVICE_NAME \
    --region $REGION \
    --limit 50

# View service details
gcloud run services describe $SERVICE_NAME \
    --region $REGION
```

### 2. Set Up Monitoring (Optional)

```bash
# Enable Cloud Monitoring API
gcloud services enable monitoring.googleapis.com

# View metrics in Console
# https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME/metrics
```

### 3. Configure Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
    --service $SERVICE_NAME \
    --domain api.yourdomain.com \
    --region $REGION
```

### 4. Enable Authentication (Production)

```bash
# Remove public access
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --no-allow-unauthenticated

# Create service account for API access
gcloud iam service-accounts create api-client \
    --display-name="API Client"

# Grant invoke permission
gcloud run services add-iam-policy-binding $SERVICE_NAME \
    --region $REGION \
    --member="serviceAccount:api-client@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

## Troubleshooting

### Common Issues

#### 1. Docker Build Fails

**Error**: `ERROR: failed to solve: process "/bin/sh -c pip install..."`

**Solution**:
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t $IMAGE_NAME:latest .
```

#### 2. Model Loading Timeout

**Error**: Service times out during startup

**Solution**:
```bash
# Increase timeout and memory
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --timeout 600 \
    --memory 4Gi \
    --cpu 4
```

#### 3. Out of Memory Errors

**Error**: Container killed due to OOM

**Solution**:
```bash
# Increase memory allocation
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --memory 4Gi
```

#### 4. Slow Response Times

**Solution**:
```bash
# Keep instances warm
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --min-instances 1 \
    --cpu 2 \
    --memory 2Gi
```

#### 5. Authentication Errors

**Error**: `Permission denied` or `403 Forbidden`

**Solution**:
```bash
# Verify service account permissions
gcloud projects get-iam-policy $PROJECT_ID \
    --flatten="bindings[].members" \
    --filter="bindings.members:serviceAccount:$SA_EMAIL"

# Re-authenticate
gcloud auth application-default login
```

#### 6. Artifact Registry Push Fails

**Error**: `denied: Permission "artifactregistry.repositories.downloadArtifacts" denied`

**Solution**:
```bash
# Grant Artifact Registry permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="user:$(gcloud config get-value account)" \
    --role="roles/artifactregistry.writer"
```

### Debugging Commands

```bash
# View recent logs
gcloud run services logs read $SERVICE_NAME \
    --region $REGION \
    --limit 100

# Stream logs in real-time
gcloud run services logs tail $SERVICE_NAME \
    --region $REGION

# Test locally with same environment
docker run -p 8000:8000 \
    -e PORT=8000 \
    $IMAGE_NAME:latest

# Check service status
gcloud run services describe $SERVICE_NAME \
    --region $REGION \
    --format="value(status.conditions)"
```

## Cost Optimization

### Free Tier Limits

- **Cloud Run**: 2 million requests/month free
- **Artifact Registry**: 0.5 GB storage free
- **Cloud Build**: 120 build-minutes/day free

### Cost Estimation

**Low Traffic** (<1000 requests/day):
- Cloud Run: ~$0.10/month
- Artifact Registry: Free
- **Total**: ~$0.10/month

**Medium Traffic** (10,000 requests/day):
- Cloud Run: ~$5-10/month
- Artifact Registry: Free
- **Total**: ~$5-10/month

**High Traffic** (100,000 requests/day):
- Cloud Run: ~$50-100/month
- Artifact Registry: ~$1/month
- **Total**: ~$50-100/month

### Optimization Tips

1. **Use min-instances=0** for cost savings (adds cold start delay)
2. **Set max-instances** based on expected load
3. **Use Cloud Run's automatic scaling**
4. **Monitor usage** via Cloud Console
5. **Set up billing alerts** to avoid surprises

## Next Steps

1. ✅ Deploy to Cloud Run
2. ✅ Test all endpoints
3. ⬜ Set up monitoring and alerting
4. ⬜ Configure custom domain
5. ⬜ Add authentication (if needed)
6. ⬜ Set up backup/restore procedures
7. ⬜ Document API for consumers
8. ⬜ Set up staging environment

## Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Guide](https://cloud.google.com/artifact-registry/docs)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [GitHub Actions with GCP](https://github.com/google-github-actions)

