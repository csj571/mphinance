#!/usr/bin/env python3
"""
CBOE Options Scanner — New Listings + Weekly Options Detector

Two detection layers:
  Layer 1: ALL OPTIONABLE — Diffs the CBOE Symbol Directory (~5000+ stocks)
           to catch when a stock gets options for the FIRST TIME (monthlies).
  Layer 2: WEEKLY OPTIONS — Diffs the CBOE Weeklys CSV (~670 tickers) to catch
           when an already-optionable stock gets promoted to weekly options.

Usage:
    python cboe_weekly_scanner.py                # Normal run (update snapshot)
    python cboe_weekly_scanner.py --dry-run      # Report changes, don't save
    python cboe_weekly_scanner.py --json          # Output diff as JSON
    python cboe_weekly_scanner.py --force-refresh # Overwrite snapshot unconditionally

Cron Example (daily at 7am):
    0 7 * * 1-5 cd /path/to/mphinance && .venv/bin/python cboe_weekly_scanner.py >> logs/cboe_scan.log 2>&1
"""

import argparse
import csv
import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
CBOE_WEEKLYS_URL = "https://www.cboe.com/available_weeklys/get_csv_download/"
CBOE_SYMBOL_DIR_URL = "https://www.cboe.com/us/options/symboldir/equity_index_options/?download=csv"
SNAPSHOT_PATH = Path(__file__).parent / "data" / "cboe_options_snapshot.json"

HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; MomentumPhund/1.0)",
    "Accept": "text/csv, text/plain, */*",
}


# ---------------------------------------------------------------------------
# CSV Fetching & Parsing
# ---------------------------------------------------------------------------

def fetch_url(url: str) -> str:
    """Download a URL and return raw text."""
    resp = requests.get(url, headers=HTTP_HEADERS, timeout=60)
    resp.raise_for_status()
    return resp.text


def parse_symbol_directory(raw: str) -> Dict[str, str]:
    """
    Parse the CBOE Symbol Directory CSV (ALL optionable stocks).

    Format: Company Name, Stock Symbol, DPM Name, Post/Station, GTH DPM
    Returns {ticker: company_name} for ~5000+ stocks.
    """
    result: Dict[str, str] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        try:
            reader = csv.reader(io.StringIO(stripped))
            row = next(reader)
        except (csv.Error, StopIteration):
            continue

        if len(row) >= 2:
            name = row[0].strip()
            ticker = row[1].strip()

            # Skip header row
            if ticker == "Stock Symbol" or name == "Company Name":
                continue
            # Skip non-ticker rows
            if not ticker or not ticker[0].isalpha():
                continue

            result[ticker] = name

    return result


def parse_weeklys_csv(raw: str) -> Dict[str, Dict[str, str]]:
    """
    Parse the CBOE Available Weeklys CSV into ETF and Equity sections.

    Returns {"etfs": {ticker: name}, "equities": {ticker: name}}
    """
    etfs: Dict[str, str] = {}
    equities: Dict[str, str] = {}
    current_section: Optional[str] = None

    for line in raw.splitlines():
        stripped = line.strip()

        # Detect section headers
        if "Exchange Traded Products" in stripped or "ETFs and ETNs" in stripped:
            current_section = "etfs"
            continue
        if stripped.startswith("Available Weeklys - Equity"):
            current_section = "equities"
            continue

        if not stripped or current_section is None:
            continue

        try:
            reader = csv.reader(io.StringIO(stripped))
            row = next(reader)
        except (csv.Error, StopIteration):
            continue

        if len(row) >= 2:
            ticker = row[0].strip()
            name = row[1].strip()
            if not ticker or not ticker[0].isalpha():
                continue
            if any(c in ticker for c in ["(", "/", " "]):
                continue

            if current_section == "etfs":
                etfs[ticker] = name
            elif current_section == "equities":
                equities[ticker] = name

    return {"etfs": etfs, "equities": equities}


# ---------------------------------------------------------------------------
# Snapshot Persistence
# ---------------------------------------------------------------------------

def load_snapshot() -> Optional[Dict]:
    """Load the previous snapshot from disk, or None if it doesn't exist."""
    if not SNAPSHOT_PATH.exists():
        return None
    try:
        with open(SNAPSHOT_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def save_snapshot(
    all_optionable: Dict[str, str],
    weekly_etfs: Dict[str, str],
    weekly_equities: Dict[str, str],
) -> None:
    """Save current listings as the new snapshot."""
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "last_updated": datetime.now().isoformat(timespec="seconds"),
        "all_optionable": all_optionable,
        "weekly_etfs": weekly_etfs,
        "weekly_equities": weekly_equities,
    }
    with open(SNAPSHOT_PATH, "w") as f:
        json.dump(snapshot, f, indent=2)


# ---------------------------------------------------------------------------
# Diff Engine
# ---------------------------------------------------------------------------

def _diff_sets(
    current: Dict[str, str],
    previous: Dict[str, str],
) -> Dict[str, Dict[str, str]]:
    """Diff two {ticker: name} dicts, returning new and removed."""
    curr_keys = set(current.keys())
    prev_keys = set(previous.keys())
    return {
        "new": {t: current[t] for t in sorted(curr_keys - prev_keys)},
        "removed": {t: previous.get(t, "?") for t in sorted(prev_keys - curr_keys)},
    }


def diff_all(
    all_optionable: Dict[str, str],
    weekly_etfs: Dict[str, str],
    weekly_equities: Dict[str, str],
    previous: Dict,
) -> Dict:
    """
    Full diff across both layers.

    Returns:
        {
            "optionable": {"new": {...}, "removed": {...}},
            "weekly_etfs": {"new": {...}, "removed": {...}},
            "weekly_equities": {"new": {...}, "removed": {...}},
        }
    """
    return {
        "optionable": _diff_sets(
            all_optionable, previous.get("all_optionable", {})
        ),
        "weekly_etfs": _diff_sets(
            weekly_etfs, previous.get("weekly_etfs", {})
        ),
        "weekly_equities": _diff_sets(
            weekly_equities, previous.get("weekly_equities", {})
        ),
    }


EMPTY_DIFF = {
    "optionable": {"new": {}, "removed": {}},
    "weekly_etfs": {"new": {}, "removed": {}},
    "weekly_equities": {"new": {}, "removed": {}},
}


# ---------------------------------------------------------------------------
# Report Generation
# ---------------------------------------------------------------------------

def generate_report(
    all_optionable: Dict[str, str],
    weekly_etfs: Dict[str, str],
    weekly_equities: Dict[str, str],
    diff: Dict,
) -> str:
    """Generate a human-readable report."""
    today = datetime.now().strftime("%Y-%m-%d")
    n_all = len(all_optionable)
    n_w_etfs = len(weekly_etfs)
    n_w_eq = len(weekly_equities)

    lines = [
        f"🔔 CBOE Options Scanner — {today}",
        "━" * 55,
        f"📊 All Optionable: {n_all}  |  Weekly ETFs: {n_w_etfs}  |  Weekly Equities: {n_w_eq}",
        "",
    ]

    has_changes = False

    # Layer 1: Newly optionable (the big one — ASM events)
    if diff["optionable"]["new"]:
        has_changes = True
        lines.append(f"🔥 NEWLY OPTIONABLE — First-Time Options ({len(diff['optionable']['new'])}):")
        for t, name in diff["optionable"]["new"].items():
            lines.append(f"  + {t:<8} — {name}")
        lines.append("")

    if diff["optionable"]["removed"]:
        has_changes = True
        lines.append(f"💀 OPTIONS REMOVED ({len(diff['optionable']['removed'])}):")
        for t, name in diff["optionable"]["removed"].items():
            lines.append(f"  - {t:<8} — {name}")
        lines.append("")

    # Layer 2: Weekly options changes
    for label, key in [("ETFs", "weekly_etfs"), ("EQUITIES", "weekly_equities")]:
        if diff[key]["new"]:
            has_changes = True
            lines.append(f"🆕 NEW WEEKLY {label} ({len(diff[key]['new'])}):")
            for t, name in diff[key]["new"].items():
                lines.append(f"  + {t:<8} — {name}")
            lines.append("")

        if diff[key]["removed"]:
            has_changes = True
            lines.append(f"❌ REMOVED WEEKLY {label} ({len(diff[key]['removed'])}):")
            for t, name in diff[key]["removed"].items():
                lines.append(f"  - {t:<8} — {name}")
            lines.append("")

    if not has_changes:
        lines.append("✅ No changes since last scan.")

    lines.append("━" * 55)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main Scan Entrypoint
# ---------------------------------------------------------------------------

def scan(
    dry_run: bool = False,
    force_refresh: bool = False,
    output_json: bool = False,
) -> Dict:
    """
    Main entrypoint: fetch both CBOE sources → diff → report → save.

    Returns structured result dict for programmatic use.
    """
    out = sys.stderr if output_json else sys.stdout

    # 1. Fetch & parse BOTH sources
    print("📡 Fetching CBOE Symbol Directory (all optionable)...", file=out)
    raw_symdir = fetch_url(CBOE_SYMBOL_DIR_URL)
    all_optionable = parse_symbol_directory(raw_symdir)
    print(f"   → {len(all_optionable)} optionable stocks", file=out)

    print("📡 Fetching CBOE Available Weeklys...", file=out)
    raw_weeklys = fetch_url(CBOE_WEEKLYS_URL)
    weeklys = parse_weeklys_csv(raw_weeklys)
    print(f"   → {len(weeklys['etfs'])} weekly ETFs, {len(weeklys['equities'])} weekly equities", file=out)

    # 2. Load previous snapshot & diff
    previous = load_snapshot()

    if previous is None:
        print("📋 No previous snapshot — creating initial baseline.", file=out)
        diff = EMPTY_DIFF
        is_initial = True
    else:
        diff = diff_all(all_optionable, weeklys["etfs"], weeklys["equities"], previous)
        is_initial = False

    # 3. Report
    report = generate_report(all_optionable, weeklys["etfs"], weeklys["equities"], diff)
    print(file=out)
    print(report, file=out)

    # 4. Save snapshot
    if not dry_run:
        save_snapshot(all_optionable, weeklys["etfs"], weeklys["equities"])
        total_changes = sum(
            len(diff[k][d]) for k in diff for d in ("new", "removed")
        )
        if is_initial:
            print("✅ Initial snapshot saved.", file=out)
        elif force_refresh:
            print("✅ Snapshot force-refreshed.", file=out)
        elif total_changes > 0:
            print(f"✅ Snapshot updated ({total_changes} change(s)).", file=out)
        else:
            print("✅ Snapshot unchanged (no diffs).", file=out)
    else:
        print("🔒 Dry run — snapshot NOT updated.", file=out)

    # Return structured result
    return {
        "date": datetime.now().isoformat(timespec="seconds"),
        "is_initial": is_initial,
        "totals": {
            "all_optionable": len(all_optionable),
            "weekly_etfs": len(weeklys["etfs"]),
            "weekly_equities": len(weeklys["equities"]),
        },
        "diff": diff,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="CBOE Options Scanner — New Listings + Weekly Options Detector"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report changes without updating the snapshot",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Overwrite snapshot unconditionally",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output diff as JSON (for pipeline integration)",
    )
    args = parser.parse_args()

    try:
        result = scan(
            dry_run=args.dry_run,
            force_refresh=args.force_refresh,
            output_json=args.output_json,
        )
    except requests.RequestException as e:
        print(f"❌ Network error fetching CBOE data: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.output_json:
        json.dump(result, sys.stdout, indent=2, default=str)
        print()


if __name__ == "__main__":
    main()
