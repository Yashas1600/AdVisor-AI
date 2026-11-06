#!/usr/bin/env bash
# deploy/gcp/deploy.sh -- Deploy AdVisor backend to Google Cloud Run
#
# !! IMPORTANT !!
# Yashas must review and approve this script before it is executed.
# Do NOT run this without explicit approval.
#
# Prerequisites:
#   - gcloud CLI installed and authenticated (gcloud auth login)
#   - Required APIs enabled (see docs/DEPLOY_GCP.md)
#   - Secrets created in Secret Manager (see below)
#
# This script is idempotent -- safe to run multiple times.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration -- edit these as needed
# ---------------------------------------------------------------------------
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-advisor-ai}"
REGION="${CLOUD_RUN_REGION:-us-central1}"
SERVICE_NAME="advisor-backend"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"
MEMORY="1Gi"
CPU="1"
MAX_INSTANCES="5"
MIN_INSTANCES="0"
CONCURRENCY="80"
TIMEOUT="300"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info() { echo "[deploy] $*"; }

# ---------------------------------------------------------------------------
# 1. Build and push container image
# ---------------------------------------------------------------------------
info "Building container image..."
gcloud builds submit \
  --project "${PROJECT_ID}" \
  --tag "${IMAGE}" \
  ../../backend

# ---------------------------------------------------------------------------
# 2. Deploy to Cloud Run
# ---------------------------------------------------------------------------
info "Deploying ${SERVICE_NAME} to Cloud Run (${REGION})..."
gcloud run deploy "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --image "${IMAGE}" \
  --platform managed \
  --allow-unauthenticated \
  --memory "${MEMORY}" \
  --cpu "${CPU}" \
  --max-instances "${MAX_INSTANCES}" \
  --min-instances "${MIN_INSTANCES}" \
  --concurrency "${CONCURRENCY}" \
  --timeout "${TIMEOUT}" \
  --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-secrets "\
GEMINI_API_KEY=GEMINI_API_KEY:latest,\
OPENAI_API_KEY=OPENAI_API_KEY:latest,\
SUPABASE_URL=SUPABASE_URL:latest,\
SUPABASE_KEY=SUPABASE_KEY:latest"

# ---------------------------------------------------------------------------
# 3. Print service URL
# ---------------------------------------------------------------------------
SERVICE_URL=$(gcloud run services describe "${SERVICE_NAME}" \
  --project "${PROJECT_ID}" \
  --region "${REGION}" \
  --format "value(status.url)")

info "Deployed successfully!"
info "Service URL: ${SERVICE_URL}"
info ""
info "Next steps:"
info "  1. Set NEXT_PUBLIC_BACKEND_URL=${SERVICE_URL} in Vercel env vars"
info "  2. Redeploy the Vercel frontend so it picks up the new URL"
info "  3. Test: curl ${SERVICE_URL}/health"
