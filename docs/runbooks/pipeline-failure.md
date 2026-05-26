# Pipeline failure runbook

> When a scheduled workflow goes red — do these things in this order.

## Step 0 — Did the notifier auto-rerun?

`notify_failure.yml` detects transient `codeload.github.com` outages
(the AC10:… error class) and auto-reruns the failed workflow ONCE.
Before debugging, check:

```bash
gh run list --workflow="<workflow name>" --limit 3
```

If you see two runs back-to-back where the second succeeded, you're
done. The `pipeline-failure` issue will close itself the next time
that workflow runs green.

## Step 1 — See the failure

```bash
# Recent failures across all workflows
gh run list --status failure --limit 10

# Drill into one
gh run view <run-id> --log-failed
```

For a fast scan: `gh run view <id> --log 2>&1 | grep -iE "error|fail|exception"`

## Step 2 — Match the failure to a known class

| Symptom in log | Class | First fix |
|---|---|---|
| `git push` returns `403` | Permissions | Add `permissions: contents: write` to the workflow's top-level block |
| `codeload.github.com` 5xx, "An action could not be found" | Transient CDN | Wait, or `gh run rerun <id>` — notify_failure auto-handles |
| `CERTIFICATE_VERIFY_FAILED: Hostname mismatch` | Wrong API host | Check the relevant secret (`TICKERTRACE_API_BASE` etc.) — `gh secret list` |
| `non-fast-forward` on push | Race between parallel cron jobs | Workflow needs `concurrency:` group or `git pull --rebase origin main` before push |
| Python `ModuleNotFoundError` | Dependency drift | Compare workflow's `pip install` line to `requirements.txt` |
| `gh: ... not found` inside step | Missing `GH_TOKEN` env | Add `env: GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}` to the step |

## Step 3 — Confirm your fix, then trigger a real run

```bash
# Validate yaml locally
gh workflow view <workflow-file> --yaml

# Trigger the workflow manually (if it has workflow_dispatch)
gh workflow run <workflow-file>

# Watch it
gh run watch
```

## Step 4 — Verify dependent outputs refreshed

Each scheduled workflow has visible artifacts:

| Workflow | Artifact / URL |
|---|---|
| `daily_dossier.yml` | [docs/reports/latest.html](../../docs/reports/latest.html), [leveraged-screener/daily.html](../../docs/leveraged-screener/daily.html) |
| `ghost_daily.yml` | [landing/blog/blog_entries.json](../../landing/blog/blog_entries.json) |
| `watchlist_dive.yml` | [docs/ticker/*/latest.html](../../docs/ticker/) |
| `update_district12.yml` | [docs/district12.html](../../docs/district12.html) |
| `triage.yml` | [STATUS.md](../../STATUS.md) |
| `deploy_pages.yml` | <https://mphinance.github.io/mphinance/> |

The leveraged-screener page has a self-rendered freshness banner — if
it shows STALE on a weekday, that's your alarm. The dossier workflow's
preflight step shows TickerTrace reachability in the run summary.

## Step 5 — Close the issue

The `pipeline-failure` label issue stays open until you manually close
it after a clean run. `gh issue close <num> --comment "Fixed in <PR or
commit>"`.

## Known fragile points

- **TickerTrace API**: external service, has had cert and host changes
  before. The dossier degrades gracefully (institutional section
  empty) but emits a `::warning::` annotation visible on the run page.
- **PyPI flakiness**: `pip install` step has no retry. Mostly fine,
  but a once-a-quarter transient can fail the dossier. Re-run.
- **GitHub Pages quota**: 10 builds/hour. The dossier + watchlist_dive
  + deploy_pages can race. Each declares a `concurrency:` group.

## Adding a new scheduled workflow?

Checklist:

- [ ] `permissions:` block declared explicitly (don't rely on defaults)
- [ ] `concurrency:` group set if it writes to the same paths as
      another workflow
- [ ] `workflow_dispatch:` trigger so you can run it manually
- [ ] Listed in `notify_failure.yml`'s `workflows:` array so failures
      get auto-rerun + tracked
- [ ] If it calls external APIs, add to the daily_dossier preflight
      pattern (or its own preflight)
