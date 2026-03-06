#!/usr/bin/env python3
"""
Stripe Checkout for The Agentic Trader's Playbook ebook.

Creates a Stripe Checkout Session for a one-time $19 purchase.
After payment, redirects to the ebook download page.

Run: uvicorn ebook_checkout:app --host 0.0.0.0 --port 8300
"""
import os
import stripe
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Stripe keys — set via environment variable or VaultGuard
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
if not stripe.api_key:
    print("[WARN] STRIPE_SECRET_KEY not set — checkout will fail")

EBOOK_FILE = os.path.join(os.path.dirname(__file__), "ebook", "the-agentic-traders-playbook.html")
DOMAIN = os.environ.get("DOMAIN", "https://mphinance.com")

app = FastAPI(title="Ebook Checkout")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


@app.post("/api/ebook/checkout")
@app.get("/api/ebook/checkout")
async def create_checkout_session():
    """Create a Stripe Checkout Session for the ebook."""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": "The Agentic Trader's Playbook",
                        "description": "8-chapter guide: AI agents + trading systems + institutional-grade tools. By mphinance.",
                        "images": [f"{DOMAIN}/img/ghost-alpha-logo.png"],
                    },
                    "unit_amount": 1900,  # $19.00
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url=f"{DOMAIN}/api/ebook/download?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{DOMAIN}/#ebook",
        )
        return RedirectResponse(session.url, status_code=303)
    except Exception as e:
        return HTMLResponse(f"<h1>Error</h1><p>{str(e)}</p>", status_code=500)


@app.get("/api/ebook/download")
async def download_ebook(session_id: str = ""):
    """Verify payment and serve the ebook."""
    if not session_id:
        return HTMLResponse("<h1>Missing session</h1>", status_code=400)

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status == "paid":
            return FileResponse(
                EBOOK_FILE,
                filename="The-Agentic-Traders-Playbook.html",
                media_type="text/html",
            )
        else:
            return HTMLResponse("<h1>Payment not complete</h1><p>Please complete payment first.</p>", status_code=402)
    except Exception as e:
        return HTMLResponse(f"<h1>Error verifying payment</h1><p>{str(e)}</p>", status_code=500)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ebook-checkout"}
