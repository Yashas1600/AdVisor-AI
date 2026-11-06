# Deploying AdVisor Backend to Google Cloud Run

This guide covers deploying the FastAPI backend to Cloud Run. The frontend stays on Vercel and the database stays on Supabase -- only the backend compute moves to GCP.

## Architecture

```
Vercel (Next.js frontend)
        |
        v  NEXT_PUBLIC_BACKEND_URL
Cloud Run (FastAPI backend)
        |
        v
Supabase (Postgres + pgvector)
```

## Prerequisites

1. **GCP project** with billing enabled.
2. **gcloud CLI** installed and authenticated:
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```
3. **Enable required APIs:**
   ```bash
   gcloud services enable \
     run.googleapis.com \
     cloudbuild.googleapis.com \
     secretmanager.googleapis.com \
     artifactregistry.googleapis.com
   ```
4. **IAM roles** on the deploying account:
   - `roles/run.admin`
   - `roles/cloudbuild.builds.editor`
   - `roles/secretmanager.admin` (one-time setup for secrets)
   - `roles/iam.serviceAccountUser`

## Step 1: Create secrets in Secret Manager

Each secret is created once. The deploy script references them by name.

```bash
echo -n "YOUR_GEMINI_KEY"   | gcloud secrets create GEMINI_API_KEY   --data-file=-
echo -n "YOUR_OPENAI_KEY"   | gcloud secrets create OPENAI_API_KEY   --data-file=-
echo -n "YOUR_SUPABASE_URL" | gcloud secrets create SUPABASE_URL     --data-file=-
echo -n "YOUR_SUPABASE_KEY" | gcloud secrets create SUPABASE_KEY     --data-file=-
```

Grant the Cloud Run service account access:

```bash
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

for SECRET in GEMINI_API_KEY OPENAI_API_KEY SUPABASE_URL SUPABASE_KEY; do
  gcloud secrets add-iam-policy-binding "${SECRET}" \
    --member="serviceAccount:${SA}" \
    --role="roles/secretmanager.secretAccessor"
done
```

## Step 2: Deploy

```bash
cd deploy/gcp
chmod +x deploy.sh
./deploy.sh
```

The script builds the container with Cloud Build, pushes it to GCR, and deploys to Cloud Run. It is idempotent -- running it again just updates the service.

### Environment variables set automatically

| Variable | Source |
|----------|--------|
| `GEMINI_API_KEY` | Secret Manager |
| `OPENAI_API_KEY` | Secret Manager |
| `SUPABASE_URL` | Secret Manager |
| `SUPABASE_KEY` | Secret Manager |
| `GOOGLE_CLOUD_PROJECT` | Set by deploy script (enables Vertex AI mode in google-genai) |
| `PORT` | Set by Cloud Run automatically |

## Step 3: Point the frontend at Cloud Run

In Vercel project settings, update:

```
NEXT_PUBLIC_BACKEND_URL=https://advisor-backend-XXXXX-uc.a.run.app
```

Redeploy the frontend for the change to take effect.

## Vertex AI mode

When `GOOGLE_CLOUD_PROJECT` is set (the deploy script does this), the `google-genai` SDK automatically uses Vertex AI for Gemini calls instead of the public API. No additional configuration is needed.

## Cost estimate

| Resource | Estimate |
|----------|----------|
| Cloud Run (1 vCPU, 1 GiB, scale-to-zero) | $0 idle; ~$5-15/mo with moderate traffic |
| Cloud Build (120 free min/day) | $0 for typical usage |
| Secret Manager (6 active secret versions) | < $0.10/mo |
| Container Registry storage | < $1/mo |
| **Total** | **~$5-15/mo under moderate load** |

Cloud Run bills per request-second with a generous free tier (2 million requests/month, 360k vCPU-seconds). With `min-instances=0` the service scales to zero when idle, so cost is near zero during development.

Compare to the legacy EC2 deployment which costs ~$30-40/mo regardless of traffic.

## Tear down

Remove the Cloud Run service and related resources:

```bash
# Delete the Cloud Run service
gcloud run services delete advisor-backend --region us-central1 --quiet

# Delete container images
gcloud container images delete gcr.io/YOUR_PROJECT_ID/advisor-backend --force-delete-tags --quiet

# Delete secrets (optional -- you may want to keep these)
for SECRET in GEMINI_API_KEY OPENAI_API_KEY SUPABASE_URL SUPABASE_KEY; do
  gcloud secrets delete "${SECRET}" --quiet
done

# Disable APIs (optional)
gcloud services disable run.googleapis.com cloudbuild.googleapis.com
```

## Legacy: EC2 deployment

The previous deployment target was AWS EC2 at `52.53.159.105:8000`. Those files are preserved for reference:

- `deploy_to_ec2.sh` -- SSH-based deploy script
- `backend/deploy/deploy.sh` -- Docker Compose deploy on EC2
- `backend/deploy/docker-compose.yml` -- Docker Compose config
- `backend/deploy/AWS_DEPLOYMENT.md` -- Full EC2 setup guide

The EC2 path is no longer actively maintained. New deployments should use Cloud Run.

## Notes

- **Supabase stays as the database.** Cloud Run connects to the same Supabase instance the EC2 backend used. No migration needed.
- **Vercel frontend** continues to work unchanged -- just update `NEXT_PUBLIC_BACKEND_URL` to the Cloud Run URL.
- **The Dockerfile** uses a non-root user and listens on `$PORT` (Cloud Run requirement). It also works locally with `docker build` and `docker run -p 8000:8000`.
- **Secrets** are injected as environment variables via Secret Manager, not baked into the image.
