#!/usr/bin/env python3
"""
Revenue Transparency — Fetch Stripe subscription revenue for landing page.

Filters for Substack subscriptions only (excludes ebook sales, one-time charges).
Outputs to landing/data/revenue_stats.json for the "Radical Transparency" widget.

Usage:
    STRIPE_SECRET_KEY=sk_live_... python3 dossier/fetch_revenue.py
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "landing" / "data" / "revenue_stats.json"


def fetch_stripe_revenue():
    """Fetch Substack subscription revenue from Stripe."""
    try:
        import stripe
    except ImportError:
        print("[ERR] pip install stripe")
        return None

    # Get key from env or gcp.secrets
    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    if not stripe.api_key:
        try:
            from gcp.secrets import get_secret
            stripe.api_key = get_secret("STRIPE_SECRET_KEY")
        except ImportError:
            pass

    if not stripe.api_key:
        print("[ERR] STRIPE_SECRET_KEY not set")
        return None

    print("═══ Revenue Transparency Fetch ═══\n")

    # ── Fetch all charges ──
    print("📊 Fetching Stripe charges...")
    all_charges = []
    has_more = True
    starting_after = None

    while has_more:
        params = {"limit": 100, "expand": ["data.invoice"]}
        if starting_after:
            params["starting_after"] = starting_after

        charges = stripe.Charge.list(**params)
        all_charges.extend(charges.data)
        has_more = charges.has_more
        if charges.data:
            starting_after = charges.data[-1].id

    print(f"  Total charges found: {len(all_charges)}")

    # ── Categorize charges ──
    substack_revenue = 0
    substack_count = 0
    other_revenue = 0
    other_count = 0
    monthly_breakdown = {}

    for charge in all_charges:
        if charge.status != "succeeded":
            continue

        amount = charge.amount / 100  # cents → dollars
        created = datetime.fromtimestamp(charge.created)
        month_key = created.strftime("%Y-%m")

        # Detect Substack subscriptions vs other charges
        # Substack charges typically come through as recurring subscription invoices
        is_substack = False

        # Check description
        desc = (charge.description or "").lower()
        if "substack" in desc or "subscription" in desc:
            is_substack = True

        # Check invoice metadata for recurring subscriptions
        if hasattr(charge, "invoice") and charge.invoice:
            invoice = charge.invoice
            if isinstance(invoice, str):
                pass  # Not expanded
            else:
                # Expanded invoice — check for subscription
                if invoice.subscription:
                    is_substack = True
                if invoice.metadata and "substack" in str(invoice.metadata).lower():
                    is_substack = True

        # Check charge metadata
        if charge.metadata:
            meta_str = str(charge.metadata).lower()
            if "substack" in meta_str:
                is_substack = True

        # Check if it's a recurring charge (subscription indicator)
        if hasattr(charge, "invoice") and charge.invoice and not is_substack:
            # If it has an invoice and it's NOT flagged as Substack,
            # it might still be a subscription — check amount patterns
            # Substack subscriptions are typically fixed amounts (e.g., $5, $8, $10/mo)
            if amount in [5, 8, 10, 15, 50, 80, 100]:  # Common Substack price points
                is_substack = True

        if is_substack:
            substack_revenue += amount
            substack_count += 1
            if month_key not in monthly_breakdown:
                monthly_breakdown[month_key] = 0
            monthly_breakdown[month_key] += amount
            print(f"  ✅ Substack: ${amount:.2f} on {created.strftime('%Y-%m-%d')} — {desc[:50]}")
        else:
            other_revenue += amount
            other_count += 1
            print(f"  ⏭️  Other:    ${amount:.2f} on {created.strftime('%Y-%m-%d')} — {desc[:50]}")

    # ── Build output ──
    stats = {
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "substack": {
            "total_revenue": round(substack_revenue, 2),
            "subscription_count": substack_count,
            "monthly": {k: round(v, 2) for k, v in sorted(monthly_breakdown.items())},
        },
        "other": {
            "total_revenue": round(other_revenue, 2),
            "charge_count": other_count,
        },
        "summary": {
            "content_revenue": round(substack_revenue, 2),
            "funded_to_brokerage": round(substack_revenue * 0.5, 2),  # "half goes to TastyTrade"
            "note": "50% of Substack revenue deposited to TastyTrade brokerage",
        },
    }

    print(f"\n{'═' * 50}")
    print(f"  Substack Revenue:   ${substack_revenue:,.2f} ({substack_count} charges)")
    print(f"  Other Revenue:      ${other_revenue:,.2f} ({other_count} charges)")
    print(f"  → Funded to TT:    ${substack_revenue * 0.5:,.2f} (50%)")
    print(f"{'═' * 50}")

    return stats


def main():
    stats = fetch_stripe_revenue()
    if not stats:
        sys.exit(1)

    # Save to landing page data
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"\n✅ Revenue stats saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
