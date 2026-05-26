# Pipeline Hardening — SPEC

> Generated 2026-05-26 against the failures of 2026-05-24/26. Goal: today's
> failure mode doesn't recur silently. Applied via the orchestrator pattern
> in [ORCHESTRATOR_PROMPT.md](ORCHESTRATOR_PROMPT.md).

## Goal

Make the mphinance GitHub Actions pipeline **resilient and observable** so
the kind of silent stale-data failure we saw today is loud and recoverable
next time. Plus a handful of process improvements that help Michael spot
problems faster.

## What we saw (the failures this pass exists to prevent)

1. `update_district12.yml` and `triage.yml` — silent 403 on `git push` for
   weeks because neither declared a `permissions:` block. Default token is
   read-only on this repo.
2. `daily_dossier.yml` — died 9s in on a transient `codeload.github.com`
   outage downloading `actions/configure-pages@v5`. No retry, manual rerun
   required, leveraged-screener page stale all day.
3. TickerTrace API base secret pointed at `api.tickertrace.mphinance.com`,
   whose TLS cert fails hostname verification. `tickertrace.py` retried 3×
   then gave up — **but the dossier reported success** because the failure
   was swallowed. Silent data degradation.
4. `docs/leveraged-screener/daily.html` had no self-displayed freshness
   signal. A visitor couldn't tell it was a day stale without inspecting
   the date in the title.

## What good looks like

- Every workflow that writes anything declares its permissions explicitly.
- Transient action-download failures retry once before failing the job.
- When an external dependency (TickerTrace) is unreachable, the workflow
  surfaces it as a visible warning or failure — not silent success.
- Generated pages display their own freshness. Stale = obvious.
- Michael gets notified (via GitHub Issue, not email-spam) when a
  scheduled workflow fails.
- A short runbook tells future-me what to check first when something
  breaks.

## Out of scope

- Migrating away from GitHub Actions / Pages.
- Rewriting `dossier/generate.py` end-to-end.
- Notification via Discord/Slack/Email (out-of-band creds, can come later).
- Touching anything under `_archive/`.
- Top-level `*.md` consolidation (Michael's call — left alone).

## Constraints

- Existing-codebase work — read [AGENTS.md](AGENTS.md), follow Sam's voice
  on commits, never `git add -A`.
- Don't break the 5AM CST weekday dossier run — verify before merging.
- All changes land via PR (current: [#5](https://github.com/mphinance/mphinance/pull/5)).

## Wave plan

- **Wave 0** — this spec + `feature_list.json`. Committed.
- **Wave 1** — Workflow hardening (perms, action pinning, retry,
  failure-notify workflow). One agent, file owner: `.github/workflows/*`.
- **Wave 2** — Code observability (TickerTrace fail-loud, screener
  freshness banner). One agent, file owners: `dossier/data_sources/*.py`.
- **Wave 3** — Runbook doc + AGENTS.md gotchas update. Inline.
- **Wave 4** — Verify (manual workflow_dispatch + curl the live URLs),
  flip `feature_list.json` items to `passes: true`, status doc.

## Acceptance

- All `feature_list.json` items at `passes: true`.
- Manual dispatch of each touched workflow succeeds.
- Tomorrow's scheduled dossier runs clean (no SSL retries in log).
