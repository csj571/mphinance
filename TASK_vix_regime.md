# Subagent Task: VIX Regime & Crash Detection Module

## Goal

Build a VIX regime detection module that can be integrated into the daily dossier pipeline. It should classify the current market environment and suggest hedging actions.

## Context

- The dossier pipeline is in `dossier/generate.py` — runs daily at 6AM CST via GitHub Actions
- Current pipeline stages are numbered (1-13). This would be a new stage
- Results should be a dict that gets passed to the report builder
- Use `yfinance` for market data (it's already installed in the venv)

## Steps

1. Create `dossier/market_regime.py` with these functions:

### `detect_regime()` → dict

Fetch and analyze:

- `^VIX` — current VIX level and 5-day change
- `^VIX3M` — 3-month VIX (VIX/VIX3M ratio < 0.85 = complacent, > 1.0 = fear)
- `^VVIX` — volatility of VIX (> 120 = unstable)
- `SPY` — current price vs 20/50/200 SMA
- Put/Call ratio if available

Classify into regimes:

```python
REGIMES = {
    "CALM": "VIX < 15, trending up — go aggressive",
    "NORMAL": "VIX 15-20, healthy market — standard sizing",
    "ELEVATED": "VIX 20-25, caution — reduce position sizes",
    "FEAR": "VIX 25-35, high vol — hedge or go to cash",
    "PANIC": "VIX > 35, crisis — protect capital, look for bottoms"
}
```

### `suggest_hedges(regime, picks)` → list

Given the regime and today's momentum picks, suggest:

- When ELEVATED+: "Consider protective puts on [gold pick]"
- When FEAR+: "Reduce position sizes to 50%, add VIX calls"
- When CALM: "Market favorable for momentum entries"

### Return format

```python
{
    "regime": "ELEVATED",
    "vix": 22.3,
    "vix_change_5d": +3.1,
    "vix_vix3m_ratio": 0.95,
    "spy_vs_sma200": -2.1,  # percent below 200 SMA
    "hedge_suggestions": ["Consider protective puts on INVA", ...],
    "market_context": "VIX elevated at 22.3 (+3.1 this week). SPY below 200 SMA..."
}
```

1. Add a simple test at the bottom:

```python
if __name__ == "__main__":
    result = detect_regime()
    print(json.dumps(result, indent=2))
```

## Python Environment

Use the venv: `/home/sam/Antigravity/empty/mphinance/venv/bin/python3`

## Output

- `dossier/market_regime.py` — the new module
- Should run standalone and print current regime + suggestions
