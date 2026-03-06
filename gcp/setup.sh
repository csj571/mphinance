# ═══════════════════════════════════════════════════════════════
# Cloud Run Job Specifications — mphinance Pipeline
#
# This file documents the Cloud Run Job configurations.
# The actual deployment happens via cloudbuild.yaml.
# ═══════════════════════════════════════════════════════════════

# ── Setup Commands ──
# Run these once to set up the GCP infrastructure.

# 1. Create Artifact Registry repo
# gcloud artifacts repositories create mphinance \
#   --repository-format=docker \
#   --location=us-central1 \
#   --description="mphinance pipeline images"

# 2. Create service account
# gcloud iam service-accounts create mphinance-pipeline \
#   --display-name="mphinance Pipeline SA"

# 3. Grant roles
# PROJECT_ID=studio-3669937961-ea8a7
# SA=mphinance-pipeline@${PROJECT_ID}.iam.gserviceaccount.com
#
# gcloud projects add-iam-policy-binding $PROJECT_ID \
#   --member="serviceAccount:$SA" \
#   --role="roles/run.admin"
#
# gcloud projects add-iam-policy-binding $PROJECT_ID \
#   --member="serviceAccount:$SA" \
#   --role="roles/secretmanager.secretAccessor"
#
# gcloud projects add-iam-policy-binding $PROJECT_ID \
#   --member="serviceAccount:$SA" \
#   --role="roles/storage.objectAdmin"
#
# gcloud projects add-iam-policy-binding $PROJECT_ID \
#   --member="serviceAccount:$SA" \
#   --role="roles/aiplatform.user"

# 4. Create secrets in Secret Manager
# echo -n "YOUR_KEY" | gcloud secrets create tradier-api-key --data-file=-
# echo -n "YOUR_KEY" | gcloud secrets create gemini-api-key --data-file=-
# echo -n "YOUR_KEY" | gcloud secrets create stripe-secret-key --data-file=-
# echo -n "mphinance-pipeline-data" | gcloud secrets create gcs-bucket-name --data-file=-

# 5. Create Cloud Scheduler triggers
# gcloud scheduler jobs create http dossier-daily \
#   --location=us-central1 \
#   --schedule="0 11 * * 1-5" \
#   --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/studio-3669937961-ea8a7/jobs/dossier-pipeline:run" \
#   --http-method=POST \
#   --oauth-service-account-email=mphinance-pipeline@studio-3669937961-ea8a7.iam.gserviceaccount.com \
#   --description="Daily dossier pipeline — 6 AM CST (11 UTC) Mon-Fri"
#
# gcloud scheduler jobs create http batch-scanner-daily \
#   --location=us-central1 \
#   --schedule="30 10 * * 1-5" \
#   --uri="https://us-central1-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/studio-3669937961-ea8a7/jobs/batch-scanner:run" \
#   --http-method=POST \
#   --oauth-service-account-email=mphinance-pipeline@studio-3669937961-ea8a7.iam.gserviceaccount.com \
#   --description="Batch scanner — 5:30 AM CST (10:30 UTC) Mon-Fri"
