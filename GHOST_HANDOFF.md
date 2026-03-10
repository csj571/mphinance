# 👻 GHOST_HANDOFF.md — Night Shift 2026-03-10 (Distribution Engine + Pipeline Polish)

## ⚠️ RESUME PRIORITY

1. **Deploy landing page to Vultr** — `rsync -avz landing/ vultr:/home/mphinance/public_html/` — regime badge, Sam quotes, blog search, dynamic stats
2. **Run pipeline dry-run** to verify all new stages fire: PipelineTimer → Summary API → Substack teaser → Discord notify → RSS feed → Track Record → git push
3. **Submit RSS feed to Google Search Console** — Sitemaps → Add sitemap → `feed.xml`
4. **Fix Gemini yolo agent loading errors** — `~/.gemini/agents/gsd-*.md` files have `skills` key Gemini doesn't recognize

---

## What Happened This Session (Night Shift)

### Data-Driven Prioritization
- GA4 data: 100% of traffic (1,116 views, 172 users) from Substack. Zero from direct sites.
- Pipeline reliability: 80% success rate (8/10 recent runs)
- Conclusion: Distribution is the bottleneck → built 4-channel auto-distribution

### Pipeline Infrastructure (Batch 1)
- **PipelineTimer** — per-stage timing + error tracking
- **Retry decorator** (`dossier/utils/retry.py`) — exponential backoff + jitter
- Wired into TickerTrace + Yahoo Finance (top 2 failure sources)
- Graceful degradation: empty data after retries, not crashes

### Distribution Engine (Batches 2-4)
- **Dossier Summary API** (`dossier/report/summary_api.py`) → `docs/api/dossier-summary.json`
  - The "atomic content unit": gold/silver/bronze picks with entry/target/stop, market snapshot, signals, Sam's quote
- **Substack Teaser** (`dossier/report/substack_teaser.py`) → `docs/substack/dossier/`
  - Auto-generates polished email with regime badge, pick table, signal counts, CTA
- **Discord Notification** (`dossier/report/discord_notify.py`) → #sam-mph
  - Daily summary post with gold pick, regime, signal count, report link
- **RSS Feed** (`dossier/report/rss_feed.py`) → `docs/feed.xml`
  - RSS 2.0 for Google indexing, Feedly, Inoreader. Auto-discovery link in archive HTML.
- **Track Record Generator** (`dossier/backtesting/track_record_generator.py`) → `docs/backtesting/track_record.json`
  - Aggregates historical picks, fetches Yahoo forward returns (1d/5d/10d/21d), computes win rate + Sharpe

### UI Polish
- **Landing:** regime badge, Sam's Quote, dynamic hero badge, pipeline_stats.json
- **Blog:** search bar with real-time filtering
- **Reports:** OG meta tags, print CSS, keyboard nav (J/K/T/?), progress bar, scroll-to-top
- **Archive:** quick-links bar (Status, Track Record, RSS, API, Substack), RSS `<link>` tag

### Pipeline Stage Changes
- All new stages wired into `dossier/generate.py`:
  - Stage 15a: Summary API → Substack Teaser → Discord Notification → RSS Feed
  - Stage 15d: Auto-Backtest
  - Stage 15e: Track Record

---

## Key Files Changed

| File | What |
|------|------|
| `dossier/generate.py` | +5 new pipeline stages |
| `dossier/utils/retry.py` | Retry decorator (NEW) |
| `dossier/report/summary_api.py` | Summary API generator (NEW) |
| `dossier/report/substack_teaser.py` | Substack email generator (NEW) |
| `dossier/report/discord_notify.py` | Discord notification (NEW) |
| `dossier/report/rss_feed.py` | RSS feed generator (NEW) |
| `dossier/report/status_page.py` | Pipeline status dashboard (NEW) |
| `dossier/backtesting/track_record_generator.py` | Track record data (NEW) |
| `docs/index.html` | Archive quick-links, RSS link |
| `landing/blog/blog_entries.json` | New Ghost Blog entry |

---

## What's Left

- [ ] Vultr deploy (landing page)
- [ ] Pipeline dry-run verification
- [ ] RSS → Google Search Console
- [ ] GA4 cross-domain tracking (mphinance.com ↔ GitHub Pages)
- [ ] Ebook checkout endpoint
- [ ] Weekly email digest summarizer
- [ ] UTM tracking on Substack CTAs
