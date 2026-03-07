# Tradier API Recipes & Streaming Reference

## WebSocket Streaming (Quotes & Trades)

### 1. Create Streaming Session
```bash
curl -X POST "https://api.tradier.com/v1/markets/events/session" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```
Returns: `{"stream": {"sessionid": "...", "url": "wss://ws.tradier.com/v1/markets/events"}}`

### 2. Connect via WebSocket
```
Endpoint: wss://ws.tradier.com/v1/markets/events
```

### 3. Send Subscription Payload
```json
{
  "symbols": ["SPY", "QQQ", "NVDA"],
  "sessionid": "SESSION_ID_FROM_STEP_1",
  "filter": ["trade", "quote", "summary"],
  "linebreak": true
}
```

### Filters
| Filter | Description |
|---|---|
| `trade` | Last trade price, size, exchange |
| `quote` | Bid/ask with sizes |
| `summary` | Open, high, low, prev close |
| `timesale` | Time & sales tick data |
| `tradex` | Extended trade info |

### Key Notes
- Session IDs are **short-lived** — use immediately after creation
- Only **one** market data stream per API key at a time
- If inactive symbols produce no data for 15 min, session auto-closes
- To modify symbols, just resend payload (no reconnect needed for WebSocket)
- If session expires, get a new one and resend payload

## Account Streaming
- Streams order events for one or more accounts
- Limited to either live OR sandbox, not both
- Currently only `trade` events are streamed

### Create Account Stream Session
```bash
curl -X POST "https://api.tradier.com/v1/accounts/events/session" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```

### Account Stream Payload
```json
{
  "sessionid": "SESSION_ID",
  "account_id": ["6YB71788"],
  "filter": ["trade"]
}
```

## REST API Quick Reference

### Get Quote
```bash
curl -H "Authorization: Bearer KEY" \
  "https://api.tradier.com/v1/markets/quotes?symbols=SPY,QQQ,NVDA"
```

### Get Options Chain
```bash
curl -H "Authorization: Bearer KEY" \
  "https://api.tradier.com/v1/markets/options/chains?symbol=SPY&expiration=2026-03-21"
```

### Get Account Balance
```bash
curl -H "Authorization: Bearer KEY" \
  "https://api.tradier.com/v1/accounts/ACCOUNT_ID/balances"
```

### Get Positions
```bash
curl -H "Authorization: Bearer KEY" \
  "https://api.tradier.com/v1/accounts/ACCOUNT_ID/positions"
```

### Place Order
```bash
curl -X POST "https://api.tradier.com/v1/accounts/ACCOUNT_ID/orders" \
  -H "Authorization: Bearer KEY" \
  -H "Accept: application/json" \
  -d "class=option&symbol=SPY&option_symbol=SPY260320C00600000&side=buy_to_open&quantity=1&type=limit&price=5.00&duration=day"
```
