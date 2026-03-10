# Batch Scanner

Automated script to run all stock screening strategies and export results to Google Sheets.

## Features

- Runs multiple screening strategies in sequence
- Sends results to Google Sheets (one tab per strategy)
- CLI options for dry-run, strategy selection
- Cron-ready for scheduled scans

---

## Setup

### 1. Install Dependencies

```bash
pip install pandas requests python-dotenv tradingview-screener yfinance scikit-learn
```

### 2. Create `.env` File

Create a `.env` file in the same directory:

```bash
# Google Sheets Integration
GOOGLE_SHEETS_WEBHOOK=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec
```

### 3. Deploy Google Apps Script

1. Create a new Google Sheet
2. Go to **Extensions → Apps Script**
3. Paste the code from `google_sheets_script_v2.js`
4. **Deploy → New Deployment → Web App**
   - Execute as: **Me**
   - Who has access: **Anyone**
5. Copy the Web App URL to your `.env`

---

## Usage

```bash
# Run all strategies and send to Sheets
python batch_scanner.py

# Dry run - print results without sending
python batch_scanner.py --dry-run

# Run specific strategies only
python batch_scanner.py --strategies "Momentum with Pullback,MEME Screen"

# List available strategies
python batch_scanner.py --list
```

---

## Available Strategies

| Strategy | Description |
|----------|-------------|
| Momentum with Pullback | Multi-timeframe EMA stack with oscillator pullback |
| Volatility Squeeze | Coiled stocks ready to break out (ATR compression) |
| MEME Screen | Top 30 by Implied Volatility from top 200 by volume |
| Small Cap Multibaggers | Quality small caps with growth + positive FCF |
| Gamma Scan | Stocks near high open interest option strikes |
| EMA Cross Momentum | Bullish EMA crossover signals |
| Bearish EMA Cross (Down) | Bearish EMA crossover signals |

---

## Cron Scheduling

Run daily at 4:00 PM (market hours) Monday-Friday:

```bash
0 16 * * 1-5 cd /path/to/project && .venv/bin/python batch_scanner.py >> logs/batch.log 2>&1
```

---

## Output

Each strategy creates its own tab in Google Sheets with:
- **ScanTime** - When the scan ran
- **Symbol** - Ticker
- **Company** - Name
- **WeekEnding** - Week ending date (for filtering)
- Strategy-specific columns (price, indicators, signals, etc.)
- **CurrentPrice** - Live price via GOOGLEFINANCE formula

---

## File Structure

```
├── batch_scanner.py           # This script
├── google_sheets_script_v2.js # Apps Script for Sheets
├── .env                       # Your webhook URL (create this)
├── .env.example               # Template
└── strategies/                # Strategy definitions
    ├── momentum.py
    ├── volatility_squeeze.py
    ├── meme_scanner.py
    └── ...
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "GOOGLE_SHEETS_WEBHOOK not configured" | Create `.env` file with your webhook URL |
| "Sheets error: 302" | Redeploy Apps Script with "Anyone" access |
| "Unknown strategy" | Run `--list` to see valid strategy names |
| Slow scans | MEME Screen and Gamma Scan fetch option data (takes time) |
