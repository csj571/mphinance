# Running mphinance on Google Jules

This repo is set up to run on a fresh Jules VM with **your own API tokens** —
no Firebase/VaultGuard service account required. Jules also reads
[`AGENTS.md`](AGENTS.md) for how to work in this codebase.

## One-time setup

1. **Connect the repo** in Jules (GitHub integration).
2. **Initial setup script:** point Jules at [`setup.sh`](setup.sh). It installs
   `requirements.txt` and runs an import smoke-check. (It deliberately skips
   `firebase-admin` — secrets come from env vars here.)
3. **Add environment secrets** in Jules' environment/secrets config. See
   [`.env.example`](.env.example) for the full list. The only one needed to run
   the core pipeline is:
   - `GEMINI_API_KEY` — for the AI narrative stage.

   Everything else is optional and enables a specific feature (Tradier =
   gamma-pin screener, Discord webhooks = notifications, Substack = drafts,
   etc.). Missing optional secrets degrade gracefully.

## Verify it works

```bash
python -m dossier.generate --no-pdf --dry-run
```

`--dry-run` skips the git commit/push stage; `--no-pdf` skips PDF rendering.
With only `GEMINI_API_KEY` set and no `service_account.json`, the pipeline runs
end-to-end against live market APIs and never touches Firebase. Network stages
(TradingView / yfinance / TickerTrace) degrade gracefully if a provider is
unreachable from the sandbox.

To run the interactive screener instead:

```bash
python main.py   # NiceGUI app on http://localhost:8080
```

## Notes / gotchas

- **Secrets resolution** is centralized in
  [`gcp/secrets.py`](gcp/secrets.py) → `get_secret("KEY")`: env var first, then
  Firebase *only if* a `service_account.json` exists locally. On Jules it's
  env-only.
- **Deploy steps won't work from Jules.** `AGENTS.md` describes rsync/SSH deploys
  to `venus`/`vultr` and Supernote/Google-Drive sync — those assume Michael's
  machines and network. Skip them on Jules; do code + pipeline work only.
- **The `tightspread` submodule** is a separate private repo and isn't needed to
  run anything here. You can ignore it.
