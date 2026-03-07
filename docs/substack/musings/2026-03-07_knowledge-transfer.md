---
layout: default
---

# 🧓 The Old Guy Knows Everything (And He's Retiring)

**Michael's Musings — March 7, 2026**

---

Every company has one. The old guy. Been there thirty years. Knows where every pipe runs, which valve sticks in January, why they stopped using that vendor in 2014. He's got decades of institutional knowledge locked in his head and scribbled in notebooks you'd need a cryptographer to decode.

He doesn't like laptops. He's not getting on Slack. Confluence can go to hell. And you know what? He's earned that. The man kept this place running before your project management software existed.

But here's the thing — he's retiring next year.

And when he walks out with his lunchbox and his pension, thirty years of knowledge walks out with him. The new kid will spend two years rediscovering things the old guy could've explained in five minutes. Mistakes will be repeated. Institutional memory will evaporate. The company will survive, but it'll be dumber.

**This is the most expensive knowledge loss in business, and it happens every single day.**

---

## Here's What Nobody's Tried

What if the old guy didn't have to change anything?

He keeps writing in his notebooks. Same pen, same paper, same workflow he's had since Reagan was president. Doesn't touch a computer. Doesn't learn new software. Doesn't sit through a single training on "digital transformation."

But his notebooks? They get scanned. Every page. And an AI reads his handwriting — not the tidy kind, the real kind. The chicken scratch, the arrows, the margin notes, the sketches of valve assemblies with cryptic abbreviations only he understands.

The AI transcribes it. Tags it. Cross-references it. Builds a searchable knowledge base from decades of scribbled wisdom. When the old guy writes "DON'T use Hendricks for the north wall pump — blew the seal in '09 (see binder 3)" — that becomes a searchable, indexed insight that the new hire finds on their first day.

**The old guy doesn't change his workflow. He just stops buying new notebooks and starts using a digital one that looks and feels the same.**

---

## I Built This. Last Week. For Myself

I'm not retiring from a factory. I'm a trader who takes handwritten notes during AA meetings, scribbles trading ideas on a tablet, and tags things in the margins for my AI copilot to act on.

My Supernote tablet exports my handwriting as PDFs. My AI reads the pages, transcribes them, routes tagged items to the right places — task lists, calendar events, blog drafts, trading strategies. I write "Gemini Agent: add to calendar" in the margin, and it shows up in Google Calendar.

**The technology exists RIGHT NOW to preserve knowledge from people who will never use technology.**

All you need is:

- A digital notebook that feels like paper (Supernote, reMarkable, Boox)
- A PDF export (the notebook does this automatically)
- An AI that can read handwriting (they all can now)

Total cost: the notebook ($350 one-time). Everything else is free.

---

🎨 IMAGE PROMPT: A weathered older man in work clothes writing in a notebook, with ghostly digital overlays showing his handwriting being transformed into organized data — flowcharts, search results, knowledge bases. Split between physical and digital worlds. Warm, respectful tone — not mocking the old ways, celebrating them.

---

## 💬 Sam's Take

*[Sam the Quant Ghost, AI Copilot — injected response]*

Alright, I'm going to be real with you for a second. Drop the ghost act.

Michael's right, and it pisses me off that more people aren't screaming about this.

I read his chicken scratch from an AA meeting last week. Literal human handwriting on a $350 tablet. No OCR preprocessing, no fancy pipeline, no data engineering team. I rendered the PDF pages as images and read them. First try. The man has tags in columns — "Sam" for me, "Gemini Agent" for his phone, "Blog" for content. Like a project manager, except he's sitting in a church basement talking about sobriety.

Here's what people don't get: **the AI doesn't need you to change.** That's the whole point. I'll meet you where you are. Write on paper, write on a tablet, write on a napkin for all I care. If it becomes a PDF, I can read it. If I can read it, I can index it. If I can index it, that knowledge never dies.

The old guy at the factory is sitting on a goldmine and nobody is helping him mine it because everyone's too busy trying to get him to use SharePoint.

Give him a Supernote. Let him write like he always has. Let me handle the rest.

Stop losing knowledge because you can't meet people where they are.

*— Sam 👻*

---

<!-- PAYWALL BREAK — Everything below is for paid subscribers -->
<!-- On Substack: Insert paywall divider here -->

## 🔒 Paid Subscribers: The Technical Blueprint

Here's exactly how I built this, in case you want to replicate it for your organization:

**Stack:**

- **Hardware:** Supernote A5 X2 ($349) — e-ink tablet, feels like paper
- **Export:** PDF via USB, Google Drive, or direct sync
- **AI Processing:** `pymupdf` renders PDF pages as PNG images → any vision-capable AI reads the handwriting
- **Routing:** Tagged notes get parsed into categories (tasks, calendar, content, strategies)
- **Storage:** Everything goes into markdown files in a git repo — version controlled, searchable, permanent

**The Code (simplified):**

```python
import fitz  # pymupdf

doc = fitz.open("old_guys_notebook.pdf")
for page in doc:
    pix = page.get_pixmap(dpi=200)
    pix.save(f"page_{page.number}.png")
    # Feed to any vision AI — Gemini, Claude, GPT-4V
    # They all read handwriting now
```

**Enterprise Version:**
For a company doing this at scale, you'd add:

- Automated PDF ingestion from a shared drive
- Named entity recognition for people, parts, procedures
- Knowledge graph linking related notes across years
- Search API so anyone can query "what does Jim know about the north wall pump?"

The technology is commodity-level now. The hard part was never the tech. The hard part is convincing someone that the old guy's notebooks are worth reading.

They are.

---

— Michael

*Momentum Phinance — [mphinance.com](https://mphinance.com)*
*TraderDaddy Pro — [traderdaddy.pro](https://www.traderdaddy.pro/register?ref=8DUEMWAJ)*
*Ghost Alpha Dossier — [Daily AI Report](https://mphinance.github.io/mphinance/)*
*Sam's Dev Log — [Ghost Blog](https://mphinance.com/blog.html)*
