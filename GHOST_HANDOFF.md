# GHOST_HANDOFF.md — Session 2026-03-06 (Afternoon)

## What Happened

### Revenue Transparency Widget (Live on mphinance.com)

- Full Stripe audit: 52 charges, $2,956.66 gross, $419.85 in fees (Substack 10% + Stripe 2.9%)
- Reconciled against Relay bank statements (Dec 2025 – Mar 2026)
- TastyTrade portfolio via API: $945.27 net liq, $144 premium income (Wheel on DDD/RR)
- 4-bucket allocation widget with delta coloring (tax was $155 short — Michael fixed in real time)
- Data in `landing/data/revenue_stats.json`, widget JS in `landing/index.html`

### VaultGuard MCP Server (Running on Venus)

- FastAPI REST API on `venus:8003` (32 secrets)
- FastMCP SSE on `venus:8004` (get_secret, list_secrets, set_secret, delete_secret)
- Firebase Firestore backend, single API key auth
- API key: stored in VaultGuard itself + in `.env` on Venus at `/home/mph/mphinance/vaultguard/.env`
- **Was initially deployed to Vultr — MOVED to Venus. Vultr fully cleaned up (container, SA, .env, iptables rules deleted)**

### GCP Cloud Run (Deployed)

- gcloud CLI installed at `/tmp/google-cloud-sdk/` (not permanent — will need reinstall)
- 6 APIs enabled on project `studio-3669937961-ea8a7`
- Artifact Registry: `mphinance-docker` (338MB pipeline image)
- GCS bucket: `mphinance-pipeline-data`
- Cloud Run Jobs: `batch-scanner` (2GB/2CPU), `dossier-pipeline` (4GB/2CPU)
- **Still needs:** Cloud Scheduler triggers, secrets wiring via VaultGuard

## Next Session Priorities

1. **Resume site refresh** — `venus:/home/mphanko/public_html/index.html` (Bootstrap 3 from 2019)
2. **Cloud Scheduler** — 5AM CST trigger for dossier-pipeline
3. **Auto-refresh revenue_stats.json** — add to dossier pipeline
4. **Point gcp/secrets.py at VaultGuard** — Venus endpoint

## Key Credentials (all in VaultGuard on Venus)

- VaultGuard API key: `vg-c565df3f42538b6bb7a0ea4a47f5afeb`
- Access: `curl -H "X-API-Key: <key>" http://venus:8003/secrets/<SECRET_NAME>`
- MCP: `http://venus:8004/sse`
