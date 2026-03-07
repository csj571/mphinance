#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
# Cloud Run & Scheduler Setup — mphinance Pipeline
# ═══════════════════════════════════════════════════════════════
set -euo pipefail

PROJECT_ID="studio-3669937961-ea8a7"
REGION="us-central1"
SA="mphinance-pipeline@${PROJECT_ID}.iam.gserviceaccount.com"

echo "═══ mphinance GCP Setup ═══"
echo "Project: $PROJECT_ID"
echo "Region:  $REGION"
echo ""

# ── 1. Artifact Registry ──
echo "[1/5] Artifact Registry..."
gcloud artifacts repositories create mphinance \
  --repository-format=docker \
  --location=$REGION \
  --description="mphinance pipeline images" \
  2>/dev/null && echo "  ✓ Created" || echo "  ✓ Already exists"

# ── 2. Service Account ──
echo "[2/5] Service Account..."
gcloud iam service-accounts create mphinance-pipeline \
  --display-name="mphinance Pipeline SA" \
  2>/dev/null && echo "  ✓ Created" || echo "  ✓ Already exists"

# ── 3. IAM Roles ──
echo "[3/5] IAM Roles..."
for ROLE in roles/run.admin roles/secretmanager.secretAccessor roles/storage.objectAdmin roles/aiplatform.user; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:$SA" \
    --role="$ROLE" \
    --quiet >/dev/null 2>&1
  echo "  ✓ $ROLE"
done

# ── 4. Secrets (skip if exist) ──
echo "[4/5] Secrets..."
echo "  ⚠ Skipping secret creation — add manually if needed:"
echo "    echo -n 'KEY' | gcloud secrets create tradier-api-key --data-file=-"
echo "    echo -n 'KEY' | gcloud secrets create gemini-api-key --data-file=-"
echo "    echo -n 'KEY' | gcloud secrets create stripe-secret-key --data-file=-"

# ── 5. Cloud Scheduler ──
echo "[5/5] Cloud Scheduler..."

gcloud scheduler jobs create http dossier-daily \
  --location=$REGION \
  --schedule="0 11 * * 1-5" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/dossier-pipeline:run" \
  --http-method=POST \
  --oauth-service-account-email=$SA \
  --description="Daily dossier pipeline — 6 AM CST (11 UTC) Mon-Fri" \
  2>/dev/null && echo "  ✓ dossier-daily created" || echo "  ✓ dossier-daily already exists"

gcloud scheduler jobs create http batch-scanner-daily \
  --location=$REGION \
  --schedule="30 10 * * 1-5" \
  --uri="https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/batch-scanner:run" \
  --http-method=POST \
  --oauth-service-account-email=$SA \
  --description="Batch scanner — 5:30 AM CST (10:30 UTC) Mon-Fri" \
  2>/dev/null && echo "  ✓ batch-scanner-daily created" || echo "  ✓ batch-scanner-daily already exists"

echo ""
echo "═══ Setup Complete ═══"
echo "Next: gcloud scheduler jobs list --location=$REGION"
