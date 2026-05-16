# TraderDaddy Ticker Sync Process

This document outlines the queries and process to automatically extract the most popular or highly-signaled tickers from the **TraderDaddy Pro** backend, so you can feed them directly into the **Ghost Alpha Dossier pipeline** on your local machine.

## What TraderDaddy is Grabbing

Based on the `admin/monitoring/signal-outcomes` page and the `platformStats` routes in TraderDaddy, there are three primary ways the platform tracks "hot" tickers:

### 1. Most Watched (Community Consensus)
This is exactly "most added to watchlist". TraderDaddy calculates this by grouping the `user_watchlists` table.
```sql
SELECT ticker, COUNT(DISTINCT user_id)::int AS watchers
FROM user_watchlists
GROUP BY ticker
ORDER BY watchers DESC
LIMIT 10;
```

### 2. Highest Signal Frequency (Algo Consensus)
This populates the "By ticker (top 25, n ≥ 5)" table on the Signal Outcomes page. It tracks which tickers have had the most options flow or smart money signals detected recently.
```sql
SELECT ticker, COUNT(*)::INT AS n
FROM signal_outcomes
-- Optional: WHERE detected_at >= NOW() - INTERVAL '7 days'
GROUP BY ticker
HAVING COUNT(*) >= 5
ORDER BY n DESC
LIMIT 25;
```

### 3. Institutional Volume (Smart Money)
TraderDaddy also calculates the most active tickers strictly by institutional flow count in the `mostInstitutionallyTradedTickers` service.

---

## 🚀 Auto-Populating Your Local Watchlist

To pull these tickers from TraderDaddy and feed them into the `mphinance` GitHub Actions pipeline, you can run a script on your local machine that queries the `newvultr` database directly (or hits an admin API endpoint) and updates your local watchlist.

### Method A: Direct Database Query via SSH (Recommended)

You can run this shell script locally. It connects to `newvultr`, runs the SQL query inside the Docker database, extracts the top 5 most watched tickers, and appends any new ones to your Ghost Alpha watchlist.

```bash
#!/bin/bash
# sync_td_watchlist.sh

# 1. Query the top 5 most watched tickers from TraderDaddy Production DB
# (Assuming the DB is running in a docker container named 'traderdaddy-db')
TICKERS=$(ssh newvultr "docker exec traderdaddy-db psql -U postgres -d traderdaddy -t -c \"
  SELECT ticker FROM user_watchlists 
  GROUP BY ticker 
  ORDER BY COUNT(DISTINCT user_id) DESC 
  LIMIT 5;
\"" | tr -d ' ' | grep -v '^$')

echo "Top TraderDaddy Tickers: $TICKERS"

# 2. Append to your local Ghost Alpha watchlist (avoiding duplicates)
WATCHLIST_FILE="/home/mph/Antigravity/mphinance/docs/watchlist.txt"

for TICKER in $TICKERS; do
    if ! grep -q "^${TICKER}$" "$WATCHLIST_FILE"; then
        echo "$TICKER" >> "$WATCHLIST_FILE"
        echo "Added $TICKER to local watchlist."
        
        # Optional: Kick off the deep dive automatically
        # python3 /home/mph/Antigravity/mphinance/dossier/generate_deep_dive.py $TICKER
    else
        echo "$TICKER is already in the watchlist."
    fi
done
```

### Method B: Create a Dedicated Admin Endpoint in TraderDaddy

If you prefer to hit an API instead of SSHing into the database:
1. In `TraderDaddy-Pro/backend/src/routes/adminPulse.ts`, add a quick route:
   ```typescript
   router.get('/hot-tickers', requireAuth, requireAdmin, async (req, res) => {
     const result = await db.query(`
       SELECT ticker FROM user_watchlists 
       GROUP BY ticker ORDER BY COUNT(DISTINCT user_id) DESC LIMIT 10
     `);
     res.json({ tickers: result.rows.map(r => r.ticker) });
   });
   ```
2. Your local Ghost Alpha system can just run a `curl` against `https://api.traderdaddy.pro/api/admin/pulse/hot-tickers` using your admin token, grab the JSON, and feed it into the dossier pipeline.

## Summary

The data you saw on the Signal Outcomes page (`signal_outcomes` table) and the Watchlist aggregates (`user_watchlists` table) are fully accessible via SQL. I've left this Markdown file here in your `mphinance` repo so you can copy the SQL snippets or the bash script whenever you're ready to wire it up to your `dossier` pipeline.
