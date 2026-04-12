# Substack Article Instructions — Momentum Phinance

> For ALL AI agents writing Substack content. Read VOICE.md first. Then follow this.

## What Works (Based on Stats)

The Q1 Earnings Report is the gold standard. It pulled the highest engagement because it nailed every single one of these:

1. **Data with personality.** Every number has a joke or a life lesson stapled to it. "$638.18 paid out all-time. That's my total compensation since launch. Comes out to $127/month. I'm not getting rich yet. That's the point."
2. **Generated infographics instead of tables.** Substack cannot render markdown tables. Period. Generate dark-theme Bloomberg-terminal-style images for any data that would normally be a table. Inline them in markdown with `![caption](filename.png)`.
3. **Real numbers from real APIs.** Not hypothetical. Not "approximately." Pull from Stripe, Tradier, Tastytrade, screener JSON. Show the receipts.
4. **Self-deprecation that builds trust.** "I saw the momentum breaking and I stayed in the bar too long." Admitting losses is the content. Perfection is boring.
5. **Recovery wisdom drops.** AA/NA references woven naturally into trading metaphors. Not forced. Not preachy. Just real.
6. **Paywall placement that gives free readers value.** Free readers should get enough to be impressed. Paid content is the live portfolio, the next trade, the insider view.

## Hard Rules (NON-NEGOTIABLE)

### Formatting
- **NO EM DASHES (—). EVER.** Restructure the sentence. Use periods, commas, colons, or semicolons instead. This is Michael's #1 pet peeve. The previous agent used exactly zero em dashes and that's the correct number.
- **NO MARKDOWN TABLES.** Substack will render them as garbage text. Generate an image instead. Dark theme. Bloomberg aesthetic. Every single time.
- **Images inline in markdown.** `![Alt text](filename.png)` format so Michael can copy-paste the whole article from the GitHub preview. All images must be generated and saved in the article directory alongside the README.md.

### Voice
- Open with the strongest, most controversial take. Not "In this article, we will discuss..."
- Short paragraphs. 3 sentences max per paragraph unless telling a story.
- Bold key numbers and takeaways. Readers skim. Make the scan worth it.
- PG-13 profanity. "bullsh*t", "damn", "hell" are fine. Keep it bar-conversation, not locker-room (save that for Discord).
- No passive voice. No hedging. No "it could be argued that."
- End with a recovery quote that ties into the market theme.

### Structure
Every Substack article follows this skeleton:

```
1. Hero image (generated, dark theme, article title + key stat)
2. Bold opener (1-2 paragraphs, hook the reader immediately)
3. Context section (what's happening in the market RIGHT NOW)
4. The meat (data + generated infographics + personality)
5. "Here's the truth..." pivot (where you teach something real)
6. <!--paywall--> (if applicable)
7. Paid-only deep dive (live data, next trades, insider view)
8. CTA (subscribe nudge, never desperate)
9. Recovery wisdom closer
10. Signature: "- Michael Hanko" or "- Michael Hanko, Managing Partner, The Phund"
```

### Image Generation Rules
- **Theme:** Dark background (#0a0a0a or #111), neon green (#00ff41) for bullish/good, gold (#f0b400) for caution, red (#e53935) for danger. Monospace or clean sans-serif fonts.
- **Style:** Bloomberg terminal meets hacker aesthetic. Data-dense but readable. No clip art. No stock photos. No rounded-corner corporate nonsense.
- **Content:** Each image should replace what would be a table or a chart. Include the actual numbers. Make it look like something a quant would have on their screen.
- **Size:** Landscape orientation (roughly 1200x600 to 1200x800). Substack renders these well.
- **Save location:** Same directory as the article README.md.

### Article Directory Structure
```
docs/articles/{article-slug}/
  README.md          # The article text (copy-paste to Substack)
  hero_banner.png    # Hero image
  infographic_1.png  # Data visual 1
  infographic_2.png  # Data visual 2
  ...
```

## What Does NOT Work

- Wall-of-text paragraphs with no images. People leave.
- Generic market commentary that anyone could write. "The market was volatile this week." No. Show the ADX at 37.5. Show what the scanner actually found.
- Tables rendered as text. They look broken on Substack and on mobile.
- Corporate tone. Nobody subscribed to read a Morgan Stanley research note.
- Clickbait with no substance. The hook has to deliver.
- Em dashes. I swear to god. Not one.

## Sam's Role

Sam writes the Ghost Blog (blog_entries.json) and Discord recaps in her sarcastic voice. But the Substack articles are written as Michael. Sam is referenced in third person ("Sam the Quant Ghost found..."). Michael is the narrator. He built the tools, he's showing the data, and he's the one with the felony record and the recovery story. That's the voice.
