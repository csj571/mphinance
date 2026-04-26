# The Momentum Phinance AI Cheat Sheet
**Mastering LLMs for Traders & Investors**

*Most people use AI like a Google search. This is how you use it like a quantitative analyst.*

---

## 1. The Three Layers of Every Prompt
An AI doesn't "think"—it predicts. Every word you write shifts the probability of what comes next.

1. **System Prompt (Role)** — Who the model is.
2. **Context** — The background data (stock prices, portfolio size, etc.).
3. **Task** — The specific format and output you want.

## 2. Universal Prompting Principles

### 🎯 Be Specific About Output Format
If you don't define the format, the AI will guess. **Define the structure before it starts writing.**

**Bad:** *"Analyze this trade."*
**Good:** 
*"Analyze this covered call setup. Format your response exactly as:*
*VERDICT: [bullish/neutral/bearish]*
*PREMIUM QUALITY: [score 1-10 with reasoning]*
*ASSIGNMENT RISK: [low/medium/high with reasoning]*
*KEY RISK: [one sentence]*
*RECOMMENDATION: [sell/wait/pass]"*

### 🎭 Role Prompting Changes Everything
Assigning a role changes the training patterns the AI activates.
- *"You are a risk manager. Review this strategy."* (Focuses on downsides)
- *"You are a quant trader trying to maximize this strategy. Review it."* (Focuses on optimization)
- *"You are a beginner investor seeing this for the first time."* (Focuses on simplicity)

### ⛓️ Chain of Thought for Complex Problems
For anything requiring reasoning (math, options greeks, probability), ask the AI to show its work.

- *"Think through this step by step before giving your final answer."*
- *"Show your reasoning. I want to see each step, not just the conclusion."*
- *"Work through this like a quant would: state assumptions, derive the formula, plug in numbers."*

### 🚧 Constraints Improve Outputs
Giving the model *less* freedom produces *better* outputs. Constraints force clarity.
- *"In 3 sentences or less:"*
- *"Without using generic adjectives:"*
- *"Assume I know options but not Python:"*

---

## 3. Plug-and-Play Prompts for Trading

### 📊 The Options Setup Review
*Use this before entering any premium-selling trade.*

```text
[ROLE] You are a strict risk manager reviewing an options trade for a retail account.

[SETUP]
Underlying: [TICKER] @ $[PRICE]
Strategy: [CSP/CC/spread]
Strike(s): $[STRIKE]
Expiration: [DATE]
Premium: $[CREDIT/DEBIT]
Account size: $[SIZE]

[TASK] Evaluate:
1. Premium quality — is this worth the risk? (annualized return %)
2. Assignment/exercise probability — realistic assessment
3. Key risk — the one thing that kills this trade
4. Regime check — does this strategy fit current market conditions?
5. Recommendation: Enter / Wait / Pass

Be direct. Give me a number where possible, not just adjectives.
```

### 🧠 The Strategy Stress-Test
*Use this when considering a new trading strategy or backtest.*

```text
[ROLE] You are a quantitative analyst reviewing a backtesting methodology.

[STRATEGY] [Describe the strategy]
[BACKTEST] [Describe what was tested and the results]

[TASK] Identify:
1. Survivorship bias risks
2. Look-ahead bias risks  
3. Overfitting indicators (too many parameters? cherry-picked timeframe?)
4. Transaction cost assumptions — are they realistic?
5. Regime dependency — when does this strategy break?

For each issue found, rate severity (critical/moderate/minor) and describe the fix.
```

---

## 4. Troubleshooting Your AI

If the AI gives you garbage, it's usually one of these three things:

1. **The Vague Ask:** "Should I sell a covered call?"
   *Fix:* Add context. "Should I sell a CC on 100 shares of NVDA (cost basis $620) with earnings in 45 days?"
2. **Missing Constraints:** The AI writes 1,000 words when you wanted a yes/no.
   *Fix:* Add a word limit or exact output format.
3. **No Role:** The AI hedges and says "this is not financial advice."
   *Fix:* Assign a persona. "You are my personal trading assistant..."

*Built for the Alpha Dossier Community by Momentum Phinance.*
