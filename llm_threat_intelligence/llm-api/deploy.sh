#!/bin/bash

# Set Google Cloud Project ID
PROJECT_ID="your-google-cloud-project-id"

# Enable necessary services
gcloud services enable run.googleapis.com

# Build and push the container
gcloud builds submit --tag gcr.io/$PROJECT_ID/llm-api

# Deploy to Cloud Run
gcloud run deploy llm-api \
    --image gcr.io/$PROJECT_ID/llm-api \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated
