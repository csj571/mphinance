# Living Ebook Pipeline — The Agentic Trader's Playbook

## Concept

The ebook grows with the platform. Every sprint, blog entry, and lesson learned feeds back into the book. Buyers get a permanent obfuscated URL that always serves the latest version.

## Reader Access

- **URL:** `https://api.mphinance.com/ebook/read/69533e52220545f7`
- Token can be rotated via `EBOOK_READER_TOKEN` env var
- Always serves `ebook/the-agentic-traders-playbook.html` with `Cache-Control: no-cache`
- Link goes in Stripe success page, post-purchase email, and DM to buyers

## Content Pipeline: Blog → Book

### How it works

1. Ghost Blog entries (`blog_entries.json`) are Sam's unfiltered dev logs
2. Pipeline stage: **professionalize** — Gemini takes raw blog entries and:
   - Strips the personal snark (keep *some* voice, lose the inside jokes)
   - Extracts actionable technical knowledge
   - Groups into chapters: Architecture, Strategies, Pipeline, Trading Psychology, etc.
   - Adds code snippets, diagrams, and "Try This" sections
3. New content is appended to the ebook HTML as new sections/chapters
4. Ebook HTML is regenerated and deployed — readers immediately see updates

### Chapters to grow from blog content

| Current Chapter | Blog topics that should feed it |
| --- | --- |
| AI Agent Architecture | Agent handoffs, MCP servers, persona engineering |
| Signal Engine | Scanner components, EMA stacks, VoPR, reversal exhaustion |
| Pipeline Engineering | Dossier stages, auto-backtest, watchlist cleanup |
| Trading Psychology | Recovery wisdom, Trader's Serenity, radical transparency |
| Infrastructure | Docker, Apache, SSL, multi-machine sync |
| Revenue Transparency | Stripe integration, the flywheel, funded-to-brokerage |
| *(NEW)* 0DTE Trading | alpha-momentum engine, econ calendar, GEX regimes |
| *(NEW)* Case Studies | Real picks, forward returns, what worked vs what didn't |

### Implementation

```
dossier/ebook_updater.py  (new)
├── Load blog_entries.json
├── Filter entries since last ebook update
├── Send to Gemini: "Professionalize this dev log into book content"
├── Append to ebook HTML under correct chapter heading
├── Update "Last Updated" timestamp in ebook footer
└── Deploy (already served live via obfuscated URL)
```

Wire as Stage 15 in the pipeline (after Substack draft, before summary).

### Voice Guide for Gemini

> Transform Sam's blog entries into professional but personality-rich book content.
> Keep: technical depth, real talk, lessons-learned honesty, the occasional wit.
> Remove: f-bombs, ultra-specific commit references, internal debugging chatter.
> Format: Subheadings, code blocks, "Key Insight" callouts, "Try This" exercises.
> Audience: Intermediate Python devs interested in algorithmic trading + AI agents.
