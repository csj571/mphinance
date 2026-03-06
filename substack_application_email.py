#!/usr/bin/env python3
"""
substack_application_email.py — The email that got sent to recruiting@substackinc.com

Sent: 2026-03-05 ~8:00 PM CST
From: contact@mphinance.com
To: recruiting@substackinc.com
CC: mphinance@gmail.com

To re-send or modify:
  python3 substack_application_email.py              # preview only
  python3 substack_application_email.py --send       # actually send
"""
import smtplib, os, sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Load secrets
secrets = {}
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets.env")
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            secrets[k] = v

SMTP_HOST = secrets.get("SMTP_HOST", "mail.privateemail.com")
SMTP_PORT = int(secrets.get("SMTP_PORT", "587"))
SMTP_USER = secrets.get("SMTP_USER", "contact@mphinance.com")
SMTP_PASS = secrets.get("SMTP_PASSWORD", "")
FROM = secrets.get("SMTP_FROM", SMTP_USER)

TO = "recruiting@substackinc.com"
CC = "mphinance@gmail.com"
SUBJECT = "Full Stack Engineer Application \u2014 I Already Build What You\u2019re Building"

HTML_BODY = """\
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 680px; line-height: 1.6; color: #222;">

<p>Hey Substack team,</p>

<p>I\u2019m Michael Hanko. I found your jobs page the way I find most interesting things \u2014 by reading the console output. That ASCII art is a nice touch.</p>

<p>I\u2019m a full-stack developer and active Substack creator (<a href="https://mphinance.substack.com">Momentum Phinance</a>). I build quant trading tools \u2014 automated pipelines, APIs, scoring engines, embeddable widgets \u2014 and I ship them fast. Today I reverse-engineered your drafts API and built a Python tool that creates Substack posts programmatically. That was a side project during a bigger session where I also rebuilt my entire analytics API, created a methodology showcase page, and consolidated 31 API keys into a Firebase-synced vault. That was one day.</p>

<p><strong>What I build:</strong></p>
<ul>
<li><strong>Ghost Alpha API</strong> \u2014 7-endpoint FastAPI service serving real-time trading analytics, Dockerized with Swagger docs (<a href="http://mphinance.com:8002/docs">live Swagger</a>)</li>
<li><strong>VoPR\u2122</strong> \u2014 Proprietary volatility analysis engine: 4-model realized vol composite, Black-Scholes Greeks, automated grading (<a href="https://mphinance.github.io/mphinance/vopr.html">methodology page</a>)</li>
<li><strong>13-stage automated pipeline</strong> \u2014 Data ingestion \u2192 scanners \u2192 AI synthesis \u2192 report generation \u2192 auto-deploy to GitHub Pages. Runs daily at 5AM CST. Zero manual intervention.</li>
<li><strong>TraderDaddy Pro</strong> \u2014 Paid alpha community on Whop (<a href="https://www.traderdaddy.pro">traderdaddy.pro</a>)</li>
<li><strong>TickerTrace Pro</strong> \u2014 ETF fund flow analytics SaaS (<a href="https://www.tickertrace.pro">tickertrace.pro</a>)</li>
</ul>

<p><strong>My stack:</strong> Python (FastAPI, pandas, matplotlib), JavaScript/TypeScript (Next.js, React), Docker, GitHub Actions CI/CD, Firebase, PostgreSQL/SQLite, Playwright for automation. I deploy to Vultr (Docker + Apache SSL) and Vercel.</p>

<p><strong>Why Substack:</strong> I use your product every day as a creator. I understand the UX from both sides \u2014 the writing experience and the reading experience. Your mission is to build a new economic engine for culture. I\u2019ve been doing the same thing in a smaller niche: building tools that let independent traders compete with institutions. Same energy, different domain. The creator economy runs on authentic, useful content \u2014 and I build the infrastructure that makes that content possible.</p>

<p><strong>The personal angle:</strong> I\u2019m in recovery. Everything I build is informed by the discipline that recovery taught me \u2014 show up daily, do the work, be honest about what\u2019s broken, fix it, repeat. My AI copilot Sam writes in the daily blog: \u201cGod, grant me the serenity to accept the trades I cannot change.\u201d That\u2019s not a joke \u2014 it\u2019s how I live and how I code. I think that perspective matters at a company that values authenticity.</p>

<p><strong>Links:</strong></p>
<ul>
<li><a href="https://mphanko.com">mphanko.com</a> \u2014 Resume & background</li>
<li><a href="https://mphinance.com">mphinance.com</a> \u2014 Product portfolio, Ghost Blog, daily picks</li>
<li><a href="https://github.com/mphinance/mphinance">GitHub</a> \u2014 Open source repo (the whole pipeline)</li>
<li><a href="https://mphinance.github.io/mphinance/vopr.html">VoPR Showcase</a> \u2014 Data product design</li>
<li><a href="http://mphinance.com:8002/docs">Ghost Alpha API</a> \u2014 Live Swagger docs</li>
<li><a href="https://mphinance.substack.com">Momentum Phinance</a> \u2014 My Substack</li>
</ul>

<p>I ship fast, I care deeply about the product, and I already live in your ecosystem. Happy to chat anytime.</p>

<p>\u2014 Michael Hanko<br>
<a href="mailto:mphanko@gmail.com">mphanko@gmail.com</a> \u00b7 <a href="https://mphanko.com">mphanko.com</a> \u00b7 <a href="https://mphinance.com">mphinance.com</a></p>

</div>
"""


def main():
    msg = MIMEMultipart("alternative")
    msg["Subject"] = SUBJECT
    msg["From"] = FROM
    msg["To"] = TO
    msg["Cc"] = CC
    msg.attach(MIMEText(HTML_BODY, "html"))

    print(f"From:    {FROM}")
    print(f"To:      {TO}")
    print(f"CC:      {CC}")
    print(f"Subject: {SUBJECT}")
    print()

    if "--send" in sys.argv:
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
                print("\u2705 Email sent successfully!")
        except Exception as e:
            print(f"\u274c Failed: {e}")
    else:
        print("[PREVIEW MODE] Run with --send to actually send")
        print(f"\nBody preview:\n{HTML_BODY[:300]}...")


if __name__ == "__main__":
    main()
