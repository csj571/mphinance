"""
GCP Secrets Manager — Runtime secret resolution for Cloud Run Jobs.

In Cloud Run, secrets are injected as environment variables via the
--set-secrets flag in cloudbuild.yaml. This module provides a fallback
chain: Secret Manager API → env var → .env file → None.

Usage:
    from gcp.secrets import get_secret
    api_key = get_secret("TRADIER_API_KEY")
"""

import os
from functools import lru_cache


@lru_cache(maxsize=32)
def get_secret(name: str, default: str = "") -> str:
    """
    Resolve a secret value with fallback chain:
    1. Environment variable (set by Cloud Run --set-secrets)
    2. Google Secret Manager API (if running on GCP with SA)
    3. Local .env file (for local development)
    4. Default value
    """
    # 1. Environment variable (fastest, Cloud Run injects these)
    value = os.environ.get(name)
    if value:
        return value

    # 2. Secret Manager API (if google-cloud-secret-manager is available)
    try:
        from google.cloud import secretmanager

        project_id = os.environ.get("GCP_PROJECT", "studio-3669937961-ea8a7")
        client = secretmanager.SecretManagerServiceClient()

        # Convert env var name to secret ID (e.g., TRADIER_API_KEY → tradier-api-key)
        secret_id = name.lower().replace("_", "-")
        secret_path = f"projects/{project_id}/secrets/{secret_id}/versions/latest"

        response = client.access_secret_version(request={"name": secret_path})
        return response.payload.data.decode("UTF-8")
    except Exception:
        pass

    # 3. Local .env file fallback
    try:
        from dotenv import dotenv_values
        env_files = ["secrets.env", ".env"]
        for env_file in env_files:
            if os.path.exists(env_file):
                values = dotenv_values(env_file)
                if name in values:
                    return values[name]
    except ImportError:
        pass

    return default


def get_all_secrets(*names: str) -> dict[str, str]:
    """Resolve multiple secrets at once."""
    return {name: get_secret(name) for name in names}


# Pre-defined secret names used across the pipeline
PIPELINE_SECRETS = [
    "TRADIER_API_KEY",
    "GEMINI_API_KEY",
    "STRIPE_SECRET_KEY",
    "GCS_BUCKET",
    "SUBSTACK_SID",
]
