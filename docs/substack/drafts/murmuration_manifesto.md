# ~~Make Me Rich~~ Make Us Rich With AI

**TLDR: Bookmark this link. Come back whenever you need it.**
**[The Full 61-Tool Open Source AI Roadmap](https://mphinance.github.io/mphinance/toolkit/index.html)**

![Make Us Rich With AI](https://raw.githubusercontent.com/mphinance/mphinance/main/docs/toolkit/campfire_hero.png)

---

I have been working on personal automation for a long time. It started with a vision of a private money machine. A few scripts, some API calls, and a lot of late nights. The plan was simple: build a proprietary fortress on top of a mountain and defend it from everyone.

It worked. Sort of. The air is thin up there. And the proprietary giants are always trying to knock you off.

I have realized that the top of the mountain is lonely if everyone else is still at the campfire below.

[Tim Denning](https://timdenning.substack.com/) has been saying this for years in a completely different context. The lone wolf grind is a lie. You do not win by building alone in a dark room. You win by building freedom alongside other people who are also building. His whole thesis at Modern Freedom is that the solo hustle narrative sold to our generation was always broken. I just needed to learn it the hard way with code instead of content.

So we are moving the operation down to the campfire.

We are evolving from personal automation to collective intelligence. This is not a solo mission anymore. It is a murmuration.

### What is Murmuration?

A murmuration is a massive, coordinated flock of starlings. Thousands of individual birds moving as one, without a central leader, through complex emergent behavior. No one tells them where to go. They react to the birds next to them. The result is something that looks choreographed but is actually decentralized intelligence.

We are applying the same principle to the markets.

### The 2026 Roadmap

I spent the last few weeks auditing the entire open source AI landscape. I filtered out the VC-backed garbage and the proprietary traps. What remains is a 100 percent FOSS roadmap for anyone who wants to build with AI in 2026.

I organized it by what I call the Complexity Gradient. It starts with one-click desktop apps for the person who has never touched a terminal, and it ends with low-level Rust frameworks for the absolute lunatics among us.

61 tools. 7 tiers. Every single one is open source. Here they are.

![The Complexity Gradient](https://raw.githubusercontent.com/mphinance/mphinance/main/docs/toolkit/complexity_gradient.png)

> **Want the interactive version?** I built a searchable, filterable dashboard with all 61 tools. You can browse by category, search by name, and click straight through to every GitHub repo.
>
> ![Dashboard Preview](https://raw.githubusercontent.com/mphinance/mphinance/main/docs/toolkit/dashboard_preview.png)
>
> **[Open the full dashboard](https://mphinance.github.io/mphinance/toolkit/index.html)**

---

### Tier 1: The Fast Casual
*Beginner friendly. One-click installs. No coding required.*

This is where everyone should start. If you have never run a local AI model before, you can be up and running in five minutes with any of these.

1. **AnythingLLM**: Full RAG stack in one installer. LLM, vector database, and document management all in one app.
2. **Ollama**: The standard for local AI. One command to download and run Llama 3, Mistral, or Phi on your own hardware.
3. **OpenWebUI**: Beautiful, self-hosted chat interface with built-in RAG and a community function store.
4. **LobeChat**: Modern chat framework focused on agent personas and high-performance UX.
5. **LibreChat**: Drop-in replacement for ChatGPT. Multi-model and highly flexible.
6. **Jan.ai**: Privacy-focused, local-first AI with a clean, minimal interface.
7. **GPT4All**: Runs powerful LLMs on consumer CPUs. No GPU required.
8. **FreedomGPT**: Uncensored local AI with a focus on absolute neutrality.
9. **Faraday**: Optimized for running character-based agent personas locally.

If you are reading [AI Supremacy](https://www.ai-supremacy.com/), you already know why local-first matters. The tools that survive are the ones you own. Not the ones that own you.

---

### Tier 2: The Home Cook
*Visual builders. Low-code. Requires some configuration.*

This is where it starts getting fun. You are not writing code yet, but you are building real workflows.

10. **Dify**: All-in-one platform for building and operating LLM apps. Visual prompt orchestrator and RAG engine.
11. **n8n**: The visual automation king. Build complex agents that talk to 400 plus external apps.
12. **Langflow**: Drag-and-drop nodes to build LangChain reasoning loops.
13. **Flowise**: Visual UI for building LangChain.js-based chatbots and memory agents.
14. **ComfyUI**: Node-based UI for complex image generation workflows (Stable Diffusion, Flux).
15. **Oobabooga**: The most feature-complete UI for local LLM testing. Supports every format.
16. **ToolJet**: Build internal dashboards with a visual low-code editor.
17. **Budibase**: Rapidly build internal apps and admin panels with built-in automation.
18. **Appsmith**: Visual platform to build custom internal tools and business apps.

[Travis Sparks at Sparkry.AI](https://sparkryai.substack.com/) writes about building AI systems that adapt to different kinds of brains. The visual builder tier is exactly that. Not everyone thinks in code. Some people think in nodes and flows and connections. These tools meet you where you are.

---

### Tier 3: The Sous-Chef
*Agentic coding. AI in your IDE. Requires developer familiarity.*

This is where AI stops being a chatbot and starts being a coworker. These tools live inside your editor, your terminal, and your Git repo.

19. **Cline**: Agentic assistant for VS Code. It sees your files, runs your terminal, and browses the web.
20. **Aider**: The definitive CLI pair programmer. Writes code and makes Git commits automatically.
21. **OpenHands**: Autonomous software engineer that can solve GitHub issues independently.
22. **CrewAI**: Framework for orchestrating collaborative groups of specialized agents.
23. **AutoGen**: Microsoft's framework for complex conversational multi-agent systems.
24. **MetaGPT**: Assigns specific software house roles to agents to build entire apps.
25. **BabyAGI**: Simplified agent framework that prioritizes and executes tasks autonomously.
26. **AutoGPT**: The original autonomous agent project for solving complex, multi-step goals.
27. **GPT Engineer**: Describe what you want to build and let the agent scaffold the codebase.

---

### Tier 4: The Pantry & Prep
*Data, Storage, and Search. The infrastructure for knowledge.*

This is the plumbing. Nobody talks about it. Everyone needs it. [Data Engineering Central](https://dataengineeringcentral.substack.com/) is the best resource I have found for understanding how to build data infrastructure that does not fall apart at scale. If you are going to build anything from Tier 5 and beyond, you need these foundations first.

28. **DuckDB**: Analytical powerhouse. SQLite on steroids for crunching gigabytes of market data on a laptop.
29. **Chroma**: Simple, open-source vector DB built for AI-native developers.
30. **Qdrant**: High-performance vector DB designed for production with metadata filtering.
31. **Weaviate**: Vector search engine with built-in vectorization and cross-modal search.
32. **Milvus**: Scalable vector database built for billion-scale embedding workloads.
33. **Firecrawl**: Turns any website into clean, LLM-ready markdown. Essential for RAG.
34. **Unstructured**: Processes PDFs, PPTs, and raw text into clean chunks for vector DBs.
35. **SearXNG**: Self-hosted metasearch engine. Privacy-focused web data for agents.
36. **Skyvern**: Vision-based browser automation for sites without an API.
37. **Farfalle**: Self-hosted Perplexity alternative for AI-powered web searching.
38. **Meilisearch**: Lightning-fast, open-source search engine for instant search UX.
39. **ClickHouse**: High-performance OLAP database for massive market data processing.
40. **Apache Arrow**: Cross-language platform for in-memory data analytics.

---

### Tier 5: The Industrial Kitchen
*Inference and Infrastructure. AI at scale.*

You are now running AI in production. These are the backends and servers that power real systems.

41. **vLLM**: High-throughput library for serving LLMs in production environments.
42. **LocalAI**: Drop-in replacement for the OpenAI API running on your own hardware.
43. **LiteLLM**: Proxy that simplifies calling 100 plus LLMs using a unified format.
44. **MetaMCP**: Aggregator for the Model Context Protocol, connecting agents to tools.
45. **OpenClaw**: Multi-channel orchestration layer for deploying agents across Discord, Slack, and Telegram.
46. **GraphRAG**: Uses knowledge graphs to enable deeper reasoning in RAG pipelines.
47. **Mem0**: Persistent memory layer that stores context across multiple agent sessions.
48. **Ray**: Unified framework for scaling AI and Python applications across a cluster.
49. **Dask**: Flexible library for parallel computing in Python for massive dataframes.
50. **Airflow**: Workflow orchestration platform to programmatically author and monitor pipelines.

If you want to understand which of these tools are actually moving the needle versus which ones are just VC press releases, [AI Made Simple by Nitin Sharma](https://aimadesimple0.substack.com/) is the translator you need. He takes the arXiv papers and the conference talks and turns them into logic you can actually implement. I would not have been able to evaluate half of this tier without publications like his.

---

### Tier 6: Molecular Gastronomy
*Expert only. Low-level optimization and high-performance quant logic.*

This is where the lunatics live. Rust-native frameworks. Compiled AI. Vectorized backtesting engines that treat your strategy as a matrix operation.

51. **DSPy**: Programmatic prompt optimization. You define the logic and let the system optimize the prompts.
52. **Ragas**: Evaluation framework to measure RAG faithfulness and relevance.
53. **Promptfoo**: Test and evaluate prompts against a suite of behavioral test cases.
54. **Langfuse**: Observability platform to trace, monitor, and analyze AI performance.
55. **Rig**: High-performance, Rust-native LLM framework for compiled AI applications.
56. **PydanticAI**: Type-safe agent framework for Python with strict data validation.
57. **VectorBT**: Vectorized backtesting engine for quants who value speed above all.
58. **Lean Engine**: Professional algorithmic trading engine connected to Interactive Brokers.
59. **ArcticDB**: Versioned DataFrame database used by hedge funds for tick data.
60. **Pandas-TA**: Comprehensive technical analysis library built on top of Pandas.
61. **TA-Lib**: Low-level library with 200 plus indicators (RSI, EMA, Bollinger, everything).

[Engineering Alpha by Sofien Kaabar](https://abouttrading.substack.com/) is the gold standard for this tier. When you need the math to back up the strategy, when you want to know if your RSI variation actually has an edge or if you are just curve-fitting in hindsight, Sofien is the person doing that work rigorously. If you are going to use VectorBT or Lean to test a strategy, read Engineering Alpha first so you know what you are testing and why.

---

### The Humans at the Campfire

Tools are just tools. Without a strategy, they are expensive space heaters. The real murmuration is not in the GitHub repos. It is in the minds that guide them.

Here are a few more people already sitting at the campfire who are worth your time.

[Yes, I give a fig by Michael Green](https://www.yesigiveafig.com/) writes macro analysis focused on the structural dynamics of liquidity and passive flows. If you want to understand why markets move the way they do at a systemic level, not just a chart level, this is the person writing about it. The tools in Tier 4 through 6 are meaningless if you do not understand the macro forces that shape the data you are feeding them.

[ETF Delta](https://theboldux.substack.com/) delivers sharp analysis on ETF flows and structural market shifts. You cannot trade the macro without understanding the plumbing, and Boldux maps the pipes better than anyone I have found.

[The Observer](https://theobservermindset.substack.com/) covers market mindset and behavioral psychology. I put this here because the best tools in the world will not save you if your head is not right. The Observer writes about the part of trading that nobody wants to talk about, and that is usually the part that matters most.

[50 Trades in 50 Weeks](https://50in50.substack.com/) is pure, actionable trading tactics and real-world market lessons. No theory. No fluff. Just the raw reality of putting risk on the table week after week and being honest about the results.

[The Black Line](https://theblacklineops.substack.com/) goes deep into market microstructure and institutional order flow mechanics. The kind of analysis that makes you rethink what you thought you knew about how markets actually work underneath the charts.

---

### Why Open Source?

Because you cannot build collective intelligence on top of a proprietary platform that can change the rules, raise the price, or shut down your access whenever it wants.

Every tool on this roadmap is FOSS. Every strategy that comes out of this community will be testable, reproducible, and transparent. We are not building a black box. We are building a glass box.

### Join the Swarm

Speed belongs to the machines. Governance belongs to the humans. Wealth belongs to the swarm.

> **Bookmark the full interactive roadmap:**
> **[https://mphinance.github.io/mphinance/toolkit/index.html](https://mphinance.github.io/mphinance/toolkit/index.html)**

Stop building alone. Pull up a chair. Start the murmuration.
