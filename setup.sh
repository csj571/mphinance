#!/usr/bin/env bash
# Environment bootstrap for fresh VMs (Google Jules, CI, local dev).
# Point Jules' "initial setup" at this script. Idempotent.
set -euo pipefail

echo "🛠  mphinance setup: installing Python dependencies..."
# Non-fatal: some base images ship a distro-managed pip that can't self-upgrade.
python3 -m pip install --upgrade pip || echo "(pip self-upgrade skipped)"
python3 -m pip install -r requirements.txt

# NOTE: firebase-admin is intentionally NOT installed here. On Jules/CI,
# secrets come from environment variables via gcp/secrets.py:get_secret().
# VaultGuard/Firebase is a local-only fallback on Michael's box.

echo "🔎 Import smoke check..."
python3 - <<'PY'
import importlib
mods = ["nicegui", "pandas", "numpy", "yfinance", "plotly", "google.genai", "jinja2"]
missing = [m for m in mods if importlib.util.find_spec(m) is None]
if missing:
    raise SystemExit(f"❌ Missing modules after install: {missing}")
from gcp.secrets import get_secret  # ensures package import works
print("✅ Core imports OK. gcp.secrets loader importable.")
PY

echo
echo "✅ Setup complete."
echo "   Set your API tokens as environment secrets (see .env.example / JULES.md)."
echo "   Verify with:  python -m dossier.generate --no-pdf --dry-run"
