"""
Pipeline Status Dashboard — Ghost Alpha Pipeline Health Monitor.

Generates a beautiful dark-terminal status page at docs/status.html
showing pipeline health metrics, per-stage timing, error history,
and ticker coverage statistics.

Auto-generated every pipeline run, persisted to docs/data/pipeline_status.json.
"""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATUS_JSON = PROJECT_ROOT / "docs" / "data" / "pipeline_status.json"
STATUS_HTML = PROJECT_ROOT / "docs" / "status.html"

MAX_HISTORY = 30  # Keep last N runs


def _load_history() -> list[dict]:
    """Load existing pipeline run history."""
    if STATUS_JSON.exists():
        try:
            with open(STATUS_JSON) as f:
                return json.load(f)
        except Exception:
            pass
    return []


def _save_history(history: list[dict]):
    """Persist pipeline run history (capped at MAX_HISTORY)."""
    STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
    history = history[-MAX_HISTORY:]
    with open(STATUS_JSON, "w") as f:
        json.dump(history, f, indent=2)


def _health_score(run: dict) -> int:
    """Calculate a 0-100 health score for a pipeline run."""
    score = 100
    errors = run.get("errors", [])
    stages = run.get("stages", {})

    # -15 per error, min 0
    score -= len(errors) * 15

    # Bonus for speed: if total < 120s, +5
    total_time = sum(s.get("duration", 0) for s in stages.values())
    if total_time < 120:
        score += 5
    elif total_time > 600:
        score -= 10

    # Bonus for coverage
    dossiers = run.get("summary", {}).get("dossiers_enriched", 0)
    if dossiers >= 6:
        score += 5
    elif dossiers == 0:
        score -= 20

    return max(0, min(100, score))


def record_run(pipeline_stats: dict) -> dict:
    """
    Record a pipeline run and return the full run entry.

    Args:
        pipeline_stats: dict with keys:
            - date: str (YYYY-MM-DD)
            - started_at: str (ISO timestamp)
            - finished_at: str (ISO timestamp)
            - total_duration: float (seconds)
            - dry_run: bool
            - stages: dict of {stage_name: {duration: float, status: str, error: str|None}}
            - errors: list of {stage: str, message: str}
            - summary: dict with {signals_count, dossiers_enriched, ticker_pages, ...}
    """
    history = _load_history()

    run = {
        "date": pipeline_stats.get("date", ""),
        "started_at": pipeline_stats.get("started_at", ""),
        "finished_at": pipeline_stats.get("finished_at", ""),
        "total_duration": round(pipeline_stats.get("total_duration", 0), 1),
        "dry_run": pipeline_stats.get("dry_run", False),
        "stages": pipeline_stats.get("stages", {}),
        "errors": pipeline_stats.get("errors", []),
        "summary": pipeline_stats.get("summary", {}),
        "health_score": _health_score(pipeline_stats),
    }

    history.append(run)
    _save_history(history)
    return run


def generate_status_page(pipeline_stats: dict = None):
    """
    Generate the docs/status.html dashboard page.

    If pipeline_stats is provided, records the run first.
    Uses the full history for the dashboard display.
    """
    if pipeline_stats:
        record_run(pipeline_stats)

    history = _load_history()
    latest = history[-1] if history else {}

    cst = ZoneInfo("America/Chicago")
    generated_at = datetime.now(cst).strftime("%Y-%m-%d %I:%M %p CST")

    # ── Build stage timing bars ──
    stages_html = ""
    if latest.get("stages"):
        max_dur = max((s.get("duration", 0) for s in latest["stages"].values()), default=1) or 1
        for name, data in latest["stages"].items():
            dur = data.get("duration", 0)
            status = data.get("status", "ok")
            pct = min(100, (dur / max_dur) * 100)

            # Color based on status
            if status == "error":
                bar_color = "#e53935"
                dot = "🔴"
            elif status == "skipped":
                bar_color = "#555"
                dot = "⏭️"
            elif dur > 60:
                bar_color = "#f0b400"
                dot = "🟡"
            else:
                bar_color = "#00ff41"
                dot = "🟢"

            stages_html += f"""
            <div class="flex items-center gap-3 text-xs group">
                <span class="w-5 text-center">{dot}</span>
                <span class="w-48 text-gray-400 truncate font-mono text-[10px]">{name}</span>
                <div class="flex-1 bg-gray-800/50 rounded-full h-2.5 overflow-hidden">
                    <div class="h-full rounded-full transition-all duration-500"
                         style="width: {pct:.0f}%; background: {bar_color}"></div>
                </div>
                <span class="w-16 text-right text-gray-500 font-mono text-[10px]">{dur:.1f}s</span>
            </div>"""

    # ── Build error log ──
    errors_html = ""
    all_errors = []
    for run in reversed(history[-10:]):
        for err in run.get("errors", []):
            all_errors.append({
                "date": run.get("date", ""),
                "stage": err.get("stage", ""),
                "message": err.get("message", "")[:120],
            })
    if all_errors:
        for e in all_errors[:8]:
            errors_html += f"""
            <div class="flex items-start gap-3 text-xs py-2 border-b border-gray-800/50">
                <span class="text-[9px] text-gray-600 font-mono whitespace-nowrap">{e['date']}</span>
                <span class="text-red-400 font-bold whitespace-nowrap">{e['stage']}</span>
                <span class="text-gray-400 truncate">{e['message']}</span>
            </div>"""
    else:
        errors_html = '<div class="text-[10px] text-gray-600 italic py-4 text-center">No errors recorded. Sam approves. 👻</div>'

    # ── Build run history dots ──
    history_dots = ""
    for run in history[-30:]:
        score = run.get("health_score", 0)
        errs = len(run.get("errors", []))
        date = run.get("date", "")
        dur = run.get("total_duration", 0)

        if errs > 2:
            dot_color = "#e53935"
        elif errs > 0:
            dot_color = "#f0b400"
        else:
            dot_color = "#00ff41"

        history_dots += f"""
            <div class="flex flex-col items-center gap-1 group relative cursor-default">
                <div class="w-3 h-3 rounded-full transition-transform hover:scale-150"
                     style="background: {dot_color}; box-shadow: 0 0 6px {dot_color}40"></div>
                <span class="text-[7px] text-gray-700 font-mono">{date[-5:] if date else ''}</span>
                <div class="absolute bottom-full mb-2 hidden group-hover:block bg-gray-900 border border-gray-700 rounded px-2 py-1 text-[9px] text-gray-300 font-mono whitespace-nowrap z-10"
                     style="box-shadow: 0 4px 12px rgba(0,0,0,0.5)">
                    Score: {score} · Errors: {errs} · {dur:.0f}s
                </div>
            </div>"""

    # ── Summary stats ──
    latest_summary = latest.get("summary", {})
    total_dur = latest.get("total_duration", 0)
    health = latest.get("health_score", 0)
    error_count = len(latest.get("errors", []))

    # Health color
    if health >= 80:
        health_color = "#00ff41"
        health_label = "HEALTHY"
    elif health >= 50:
        health_color = "#f0b400"
        health_label = "DEGRADED"
    else:
        health_color = "#e53935"
        health_label = "CRITICAL"

    # Avg health across history
    avg_health = 0
    if history:
        avg_health = sum(r.get("health_score", 0) for r in history) / len(history)

    # Success rate
    success_runs = sum(1 for r in history if len(r.get("errors", [])) == 0)
    success_rate = (success_runs / len(history) * 100) if history else 0

    # ── Heartbeat animation ──
    heartbeat_class = "animate-pulse" if health >= 50 else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PIPELINE.STATUS // Ghost Alpha</title>
    <meta name="description" content="Ghost Alpha Dossier Pipeline health dashboard — live status, stage timing, and error tracking.">
    <meta property="og:title" content="Pipeline Status // Ghost Alpha">
    <meta property="og:description" content="Real-time health monitoring for the Ghost Alpha Dossier pipeline.">
    <meta property="og:type" content="website">
    <link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            theme: {{
                extend: {{
                    fontFamily: {{
                        'mono': ['"JetBrains Mono"', 'monospace'],
                        'tech': ['"Share Tech Mono"', 'monospace'],
                    }},
                    colors: {{
                        'neon-green': '#00ff41',
                        'neon-red': '#ff3e3e',
                        'neon-blue': '#00f3ff',
                        'neon-amber': '#ffb000',
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{
            background-color: #050505;
            color: #e0e0e0;
            font-family: 'JetBrains Mono', monospace;
            background-image:
                linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%),
                linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06));
            background-size: 100% 2px, 3px 100%;
        }}
        .hud-panel {{
            background: rgba(10, 10, 10, 0.8);
            border: 1px solid #333;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
        }}
        @keyframes heartbeat {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            25% {{ transform: scale(1.15); opacity: 0.9; }}
            50% {{ transform: scale(1); opacity: 1; }}
            75% {{ transform: scale(1.08); opacity: 0.95; }}
        }}
        .heartbeat {{ animation: heartbeat 2s ease-in-out infinite; }}
        @keyframes scan {{
            0% {{ top: -100px; }}
            100% {{ top: 100%; }}
        }}
        .scanline {{
            width: 100%; height: 100px; z-index: 10;
            background: linear-gradient(0deg, transparent, rgba(0, 255, 65, 0.03), transparent);
            position: fixed; top: 0;
            animation: scan 8s linear infinite;
            pointer-events: none;
        }}
        @keyframes glow {{
            0%, 100% {{ box-shadow: 0 0 20px {health_color}20, 0 0 40px {health_color}10; }}
            50% {{ box-shadow: 0 0 30px {health_color}30, 0 0 60px {health_color}15; }}
        }}
        .health-glow {{ animation: glow 3s ease-in-out infinite; }}
        .uptime-bar {{ transition: width 0.5s ease-out; }}
    </style>
</head>
<body class="min-h-screen p-4 md:p-8">
    <div class="scanline"></div>
    <div class="max-w-5xl mx-auto space-y-5">

        <!-- ═══ HEADER ═══ -->
        <div class="hud-panel p-6 rounded-sm border-l-4 border-neon-green">
            <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 class="text-2xl md:text-3xl font-black font-tech tracking-widest text-white uppercase italic">
                        PIPELINE.STATUS <span style="color: {health_color}">●</span>
                    </h1>
                    <p class="text-[10px] text-gray-500 uppercase tracking-[0.3em] mt-1">
                        Ghost Alpha Dossier — System Health Monitor // {generated_at}
                    </p>
                </div>
                <div class="flex items-center gap-4">
                    <a href="reports/latest.html" class="px-3 py-1.5 bg-neon-blue/10 text-neon-blue border border-neon-blue/30 text-[10px] font-mono uppercase hover:bg-neon-blue/20 transition-colors rounded">
                        Latest Report →
                    </a>
                    <a href="index.html" class="px-3 py-1.5 bg-gray-800 text-gray-400 border border-gray-700 text-[10px] font-mono uppercase hover:text-white transition-colors rounded">
                        Archive
                    </a>
                </div>
            </div>
        </div>

        <!-- ═══ HEALTH SCORE + VITALS ═══ -->
        <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
            <!-- Big Health Score -->
            <div class="md:col-span-1 hud-panel p-6 rounded-sm flex flex-col items-center justify-center health-glow">
                <div class="text-[9px] text-gray-600 uppercase tracking-widest mb-2">Health Score</div>
                <div class="heartbeat text-5xl font-black font-tech" style="color: {health_color}">
                    {health}
                </div>
                <div class="text-[10px] uppercase tracking-widest mt-2 font-bold" style="color: {health_color}">
                    {health_label}
                </div>
            </div>

            <!-- Vitals Grid -->
            <div class="md:col-span-3 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Last Run</div>
                    <div class="text-sm font-bold text-neon-blue font-mono mt-1">{latest.get('date', '—')}</div>
                    <div class="text-[9px] text-gray-600 mt-1">{latest.get('started_at', '—')[-8:] if latest.get('started_at') else '—'}</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Duration</div>
                    <div class="text-sm font-bold text-white font-mono mt-1">{total_dur:.0f}s</div>
                    <div class="text-[9px] text-gray-600 mt-1">{total_dur / 60:.1f} min</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Errors</div>
                    <div class="text-sm font-bold font-mono mt-1 {'text-neon-green' if error_count == 0 else 'text-red-400'}">{error_count}</div>
                    <div class="text-[9px] text-gray-600 mt-1">this run</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Success Rate</div>
                    <div class="text-sm font-bold font-mono mt-1 {'text-neon-green' if success_rate >= 80 else 'text-neon-amber' if success_rate >= 50 else 'text-red-400'}">{success_rate:.0f}%</div>
                    <div class="text-[9px] text-gray-600 mt-1">{success_runs}/{len(history)} runs</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Signals</div>
                    <div class="text-sm font-bold text-neon-green font-mono mt-1">{latest_summary.get('signals_count', '—')}</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Dossiers</div>
                    <div class="text-sm font-bold text-neon-amber font-mono mt-1">{latest_summary.get('dossiers_enriched', '—')}</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Ticker Pages</div>
                    <div class="text-sm font-bold text-neon-blue font-mono mt-1">{latest_summary.get('ticker_pages', '—')}</div>
                </div>
                <div class="hud-panel p-4 rounded-sm text-center">
                    <div class="text-[9px] text-gray-600 uppercase">Avg Health</div>
                    <div class="text-sm font-bold font-mono mt-1 {'text-neon-green' if avg_health >= 80 else 'text-neon-amber' if avg_health >= 50 else 'text-red-400'}">{avg_health:.0f}</div>
                    <div class="text-[9px] text-gray-600 mt-1">{len(history)} runs</div>
                </div>
            </div>
        </div>

        <!-- ═══ RUN HISTORY (last 30) ═══ -->
        <div class="hud-panel p-4 rounded-sm">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-800 pb-2">
                📈 RUN.HISTORY <span class="text-neon-blue">// LAST {len(history)} RUNS</span>
            </div>
            <div class="flex items-end gap-1.5 justify-center flex-wrap py-2">
                {history_dots}
            </div>
            <div class="flex justify-between text-[8px] text-gray-700 mt-2 px-4">
                <span>← Oldest</span>
                <span>🟢 Clean &nbsp; 🟡 Warnings &nbsp; 🔴 Errors</span>
                <span>Latest →</span>
            </div>
        </div>

        <!-- ═══ STAGE TIMING ═══ -->
        <div class="hud-panel p-4 rounded-sm border-t-2 border-neon-green">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-4 border-b border-gray-800 pb-2">
                ⏱️ STAGE.TIMING <span class="text-neon-green">// LAST RUN BREAKDOWN</span>
            </div>
            <div class="space-y-2">
                {stages_html if stages_html else '<div class="text-[10px] text-gray-600 italic py-4 text-center">No timing data yet. Run the pipeline first.</div>'}
            </div>
            <div class="text-right text-[9px] text-gray-600 mt-3 font-mono">
                Total: {total_dur:.1f}s ({total_dur / 60:.1f} min)
            </div>
        </div>

        <!-- ═══ ERROR LOG ═══ -->
        <div class="hud-panel p-4 rounded-sm border-t-2 {'border-red-500' if all_errors else 'border-gray-700'}">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">
                {'🔴' if all_errors else '✅'} ERROR.LOG <span class="{'text-red-400' if all_errors else 'text-neon-green'}">// {'RECENT ERRORS' if all_errors else 'ALL CLEAR'}</span>
            </div>
            {errors_html}
        </div>

        <!-- ═══ PIPELINE COVERAGE ═══ -->
        <div class="hud-panel p-4 rounded-sm">
            <div class="text-[10px] text-gray-500 uppercase tracking-widest mb-3 border-b border-gray-800 pb-2">
                📊 COVERAGE.STATS <span class="text-neon-amber">// WHAT THE PIPELINE PRODUCED</span>
            </div>
            <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                <div class="bg-black/40 border border-gray-800 rounded p-3 text-center">
                    <div class="text-[8px] text-gray-600 uppercase">Market Pulse</div>
                    <div class="text-lg font-bold text-neon-blue font-mono">{latest_summary.get('market_pulse', '—')}</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3 text-center">
                    <div class="text-[8px] text-gray-600 uppercase">Signals</div>
                    <div class="text-lg font-bold text-neon-green font-mono">{latest_summary.get('signals_count', '—')}</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3 text-center">
                    <div class="text-[8px] text-gray-600 uppercase">Dossiers</div>
                    <div class="text-lg font-bold text-neon-amber font-mono">{latest_summary.get('dossiers_enriched', '—')}</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3 text-center">
                    <div class="text-[8px] text-gray-600 uppercase">Setups</div>
                    <div class="text-lg font-bold text-white font-mono">{latest_summary.get('technical_setups', '—')}</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3 text-center">
                    <div class="text-[8px] text-gray-600 uppercase">CSP Picks</div>
                    <div class="text-lg font-bold text-white font-mono">{latest_summary.get('csp_setups', '—')}</div>
                </div>
                <div class="bg-black/40 border border-gray-800 rounded p-3 text-center">
                    <div class="text-[8px] text-gray-600 uppercase">Charts</div>
                    <div class="text-lg font-bold text-white font-mono">{latest_summary.get('charts_generated', '—')}</div>
                </div>
            </div>
        </div>

        <!-- ═══ FOOTER ═══ -->
        <div class="text-center py-4 space-y-2">
            <div class="text-[10px] text-gray-600 font-mono">
                Sam watches everything. The pipeline watches the market. This page watches the pipeline.
                <br>It's watchers all the way down. 👻
            </div>
            <div class="text-[9px] text-gray-700 font-mono uppercase tracking-widest">
                Ghost Alpha Pipeline Status // Generated {generated_at}
            </div>
            <div class="flex justify-center gap-4 mt-2">
                <a href="https://mphinance.com" class="text-[9px] text-gray-600 hover:text-neon-blue transition-colors">mphinance.com</a>
                <a href="https://github.com/mphinance/mphinance" class="text-[9px] text-gray-600 hover:text-white transition-colors">GitHub</a>
                <a href="https://mphinance.com/blog/" class="text-[9px] text-gray-600 hover:text-purple-400 transition-colors">Ghost Blog</a>
            </div>
        </div>

    </div>
</body>
</html>"""

    STATUS_HTML.parent.mkdir(parents=True, exist_ok=True)
    with open(STATUS_HTML, "w") as f:
        f.write(html)

    print(f"  ✓ Status dashboard: {STATUS_HTML}")
    return str(STATUS_HTML)
