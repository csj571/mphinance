"""Centralized secret loader for the mphinance pipeline.

Single source of truth for fetching secrets. **Environment variables first** —
this is what makes the repo runnable on fresh VMs (Google Jules, CI, Cloud Run)
where the operator supplies their own API tokens. The legacy Firebase
"VaultGuard" backend is consulted *only* when a service-account file is present
(i.e. Michael's local box), and any failure there degrades silently to the
default. Nothing in here raises.

Usage:
    from gcp.secrets import get_secret
    key = get_secret("GEMINI_API_KEY")
"""

import os
from pathlib import Path

# Where a Firebase service account would live, if this is a VaultGuard host.
# Override with FIREBASE_CREDENTIALS; otherwise look for service_account.json
# at the repo root. On Jules/CI neither exists, so Firebase is never touched.
_DEFAULT_SA = Path(__file__).resolve().parent.parent / "service_account.json"


def get_secret(key: str, default: str = "") -> str:
    """Return secret ``key`` from the environment, falling back to VaultGuard.

    Resolution order:
      1. ``os.environ[key]`` — the canonical source on Jules/CI/Cloud Run.
      2. Firebase Firestore ``secrets`` collection — only if a service-account
         file exists locally. Best-effort; any error returns ``default``.
    """
    val = os.environ.get(key)
    if val:
        return val

    sa = os.environ.get("FIREBASE_CREDENTIALS") or str(_DEFAULT_SA)
    if Path(sa).exists():
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore

            if not firebase_admin._apps:
                firebase_admin.initialize_app(credentials.Certificate(sa))
            doc = firestore.client().collection("secrets").document(key).get()
            if doc.exists:
                return doc.to_dict().get("value", default)
        except Exception:
            # No firebase-admin installed, bad creds, network error, etc.
            # Env vars are the supported path; fall through to default.
            pass
    return default
