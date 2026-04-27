# 🤖 Sam: Discord Prompts Master Guide

Welcome to the official prompt guide for **Sam**, your resident quantitative trading AI. 

This guide provides tested, copy-paste ready examples of how to interact with Sam to get the most out of his advanced toolchain. Sam has access to real-time stock screening, historical data, deep technicals, institutional options flow (VoPR), and a massive **139-book quantitative trading library**.

---

## 📚 1. Tapping the 139-Book Knowledge Base (Behavioral & Strategic)
Sam has ingested 139 classic trading books (e.g., *Trading in the Zone*, *Naked Forex*, *Options Field Manual*). You can ask him to synthesize trading rules, analyze psychology, or pull specific strategies.

**Prompt Examples:**
> "@Sam I keep revenge trading after taking a loss. Search your 139-book knowledge base for Mark Douglas's advice in 'Trading in the Zone' on how to accept risk, and give me a 3-step checklist to follow before my next trade."

> "@Sam I'm trying to understand the 'Volume Price Analysis' methodology. Query your library for the core concepts of VPA and explain how I should interpret a high-volume doji at the top of a trend."

> "@Sam What are the top 3 rules for managing risk during high VIX environments? Synthesize the answers strictly from the hedge fund and options manuals in your database."

**What to Expect:** Sam will query the ChromaDB RAG system, pull direct passages from the books, and synthesize a structured, expert-level response without hallucinating.

---

## 🕵️ 2. The Dossier: Discord Chat History
Sam automatically ingests all chat history from the Discord server. He knows what everyone has traded, bragged about, or panicked over.

**Prompt Examples:**
> "@Sam Query the dossier. What was the general sentiment in the chat about $NVDA right before earnings last quarter? Was everyone overly bullish?"

> "@Sam Look up my recent chat history regarding $SPY zero-DTE options. Roast my trading psychology based on what I've been saying."

> "@Sam Has anyone in the server been talking about unusual flow in $PLTR today? Check the history from the last 24 hours."

**What to Expect:** Sam will retrieve recent/historical messages from the database and provide a summary (or a witty roast) based on actual community chatter.

---

## 📈 3. Momentum Stock Screening
Use Sam to instantly run screens across the market to find setups.

**Prompt Examples:**
> "@Sam Run a screen for tech stocks that are currently heavily oversold on the daily RSI, but have a high relative volume today. Give me the top 5 tickers."

> "@Sam Give me a list of the top 10 stocks making new 52-week highs with an average daily volume over 2 million."

> "@Sam I'm looking for CANSLIM setups. Screen the market for stocks breaking out of consolidations on 200%+ relative volume. Display the results in a table."

**What to Expect:** A neatly formatted table of tickers matching the criteria, complete with current prices, volume metrics, and relevant indicators.

---

## 📊 4. Technical Analysis & Charting
Instead of opening TradingView, ask Sam to calculate the exact technical state of a ticker.

**Prompt Examples:**
> "@Sam Give me a full technical breakdown of $TSLA. I want the MACD, the 14-day RSI, the ATR, and tell me if it's trading above its 50-day and 200-day EMAs."

> "@Sam Analyze $AMD's daily chart for the last 3 months. Are there any hidden bullish divergences between the price action and the RSI?"

> "@Sam Generate a candlestick chart for $COIN over the last 30 days and analyze the key support and resistance levels based on volume profile."

**What to Expect:** A detailed breakdown of the requested indicators, identifying whether the stock is in a bullish/bearish regime, and (if requested) a generated image chart.

---

## 🎯 5. Options, Greeks, and VoPR Engine
Sam is directly hooked into the proprietary VoPR engine and TraderDaddy institutional flow.

**Prompt Examples:**
> "@Sam What is the current VoPR score for $SPX? Break down the call/put delta exposure and tell me where the heaviest dealer gamma walls are located for this Friday's expiration."

> "@Sam I'm looking to sell cash-secured puts on $AAPL. Check the options chain for 30-45 DTE and find the strike with a .15 to .20 delta. What's the premium and the annualized return on capital?"

> "@Sam Scan for unusual institutional options flow today. Are whales aggressively buying calls on any specific semiconductor names?"

**What to Expect:** Advanced options analysis, including real-time Greeks, institutional flow imbalances, and specific strike/expiration data formatted clearly.

---

## 🛠️ 6. Combine & Conquer (Advanced Prompts)
The true power of Sam comes from combining tools in a single prompt.

**Prompt Examples:**
> "@Sam First, run a screen for the most overbought stocks in the S&P 500. Pick the top result, run a full technical analysis on it to confirm exhaustion, and then check the options chain for the cost of an at-the-money put expiring in 2 weeks."

> "@Sam Check the Discord dossier to see what ticker people are most hyped about today. Then, run that ticker through the VoPR engine to see if institutional options flow agrees with the retail hype, and give me your final verdict."

> "@Sam Pull the historical price data for $META during its last earnings drop. Then, search the 139-book knowledge base for rules on 'buying the dip' and tell me if the current setup on $META matches those textbook rules."

---
> [!TIP]
> **Pro-Tip for Best Results:** Always be specific with timeframes (e.g., "daily chart", "last 6 months") and indicator settings. If you want a table, explicitly ask Sam to "format the results as a markdown table."
