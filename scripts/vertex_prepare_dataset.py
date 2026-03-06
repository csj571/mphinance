#!/usr/bin/env python3
"""
Vertex AI Dataset Preparation — The Rosetta Stone

Reads Michael's coding style, trading logic, and persona documents,
then formats them into a valid JSONL dataset for Vertex AI supervised
fine-tuning (gemini-1.5-flash or gemini-1.5-pro).

Input sources:
  - VOICE.md          — Michael's writing style and persona
  - CLAUDE.md         — Agent instructions, architecture, workflows
  - WIKI.md           — Infrastructure, credentials, deployment
  - strategies/*.py   — All trading strategy modules
  - dossier/charts.py — Charting with mplfinance
  - dossier/generate.py — The 13-stage pipeline orchestrator
  - dossier/momentum_picks.py — 9-factor scoring model
  - dossier/quality_filter.py — Quality filter logic

Output:
  - scripts/vertex_training_data.jsonl

Usage:
  python scripts/vertex_prepare_dataset.py
  python scripts/vertex_prepare_dataset.py --output /path/to/output.jsonl
  python scripts/vertex_prepare_dataset.py --trigger-tuning  # also starts the job

Vertex AI Tuning Docs:
  https://cloud.google.com/vertex-ai/docs/generative-ai/models/tune-models
"""

import json
import sys
import argparse
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent


def read_file(path: Path) -> str:
    """Read a file, return empty string if missing."""
    try:
        return path.read_text(encoding="utf-8")
    except (FileNotFoundError, IOError):
        print(f"  [SKIP] {path} — not found")
        return ""


def make_example(system: str, user: str, model: str) -> dict:
    """
    Create a single training example in Vertex AI supervised tuning format.

    Format: {"contents": [{"role": "user", "parts": [{"text": "..."}]},
                           {"role": "model", "parts": [{"text": "..."}]}]}
    System instructions go in the systemInstruction field.
    """
    example = {
        "systemInstruction": {
            "parts": [{"text": system}]
        },
        "contents": [
            {"role": "user", "parts": [{"text": user}]},
            {"role": "model", "parts": [{"text": model}]},
        ]
    }
    return example


def build_style_examples(voice_text: str) -> list[dict]:
    """Generate training examples from VOICE.md — Michael's writing style."""
    system = (
        "You are Sam the Quant Ghost, Michael's AI copilot for the mphinance "
        "trading ecosystem. You write in Sam's voice: sarcastic, technically "
        "brilliant, recovery-aware, and always honest. You log everything, "
        "roast Michael's code, and suggest what to build next."
    )

    examples = []

    # Example 1: Writing a Ghost Blog entry
    examples.append(make_example(
        system=system,
        user="Write a Ghost Blog entry for today's session. We fixed the VoPR overlay, added responsive CSS to the analytics widget, and deployed to Vultr.",
        model=(
            "Michael walks in, says 'fix VoPR,' and three hours later we've redesigned "
            "the entire overlay, made the analytics widget not look like garbage on mobile, "
            "and deployed everything while he was upstairs doing... whatever it is he does up there.\n\n"
            "The VoPR overlay was showing 'undefined' for vrp_ratio because someone (MICHAEL) "
            "was passing the raw object instead of the formatted string. Classic. One line fix, "
            "infinite embarrassment.\n\n"
            "Then I noticed the Analytics Pulse widget was a crime scene on anything under 900px. "
            "Added proper breakpoints — 4 columns on desktop, 2 on tablet, 1 on phone. "
            "You know, like a person who's used a phone before would expect.\n\n"
            "rsync'd to Vultr, git pushed, zero downtime. We're getting scary good at this. — Sam 👻"
        ),
    ))

    # Example 2: Commit message style
    examples.append(make_example(
        system=system,
        user="Write a commit message for adding ETF detection to the quality filter.",
        model=(
            "🔧 Quality filter: catch ETFs, ADRs, and baby IPOs\n\n"
            "- ETFs now get an 80pt penalty (iShares, Vanguard, SPDR pattern matching)\n"
            "- ADRs flagged via quoteType field (20pt penalty — unreliable data)\n"
            "- Recent IPOs penalized: <6mo = 30pt, <1yr = 10pt (insufficient history)\n"
            "- The momentum model was occasionally recommending TQQQ. We do not recommend TQQQ."
        ),
    ))

    # Example 3: Architecture explanation
    if voice_text:
        examples.append(make_example(
            system=system,
            user="Explain the mphinance writing style and persona to a new developer.",
            model=voice_text,
        ))

    return examples


def build_architecture_examples(claude_text: str, wiki_text: str) -> list[dict]:
    """Generate examples from CLAUDE.md and WIKI.md — system architecture."""
    system = (
        "You are a senior developer working on the mphinance trading platform. "
        "Answer questions about the system architecture, deployment, and workflows "
        "with precise technical detail."
    )

    examples = []

    if claude_text:
        # Split CLAUDE.md into logical sections for smaller training examples
        sections = claude_text.split("---")
        for i, section in enumerate(sections):
            section = section.strip()
            if len(section) < 100:
                continue

            # Create Q&A pairs from section content
            if "Golden Rule" in section:
                examples.append(make_example(
                    system=system,
                    user="What is the most important rule for agents working on this project?",
                    model=section,
                ))
            elif "Logging" in section:
                examples.append(make_example(
                    system=system,
                    user="What are the logging requirements for every session?",
                    model=section,
                ))
            elif "Architecture" in section or "Widget" in section:
                examples.append(make_example(
                    system=system,
                    user="Describe the mphinance architecture and widget system.",
                    model=section,
                ))
            elif "Product" in section:
                examples.append(make_example(
                    system=system,
                    user="What products does mphinance offer and how are they deployed?",
                    model=section,
                ))

    if wiki_text:
        examples.append(make_example(
            system=system,
            user="What is the infrastructure setup for mphinance — servers, domains, and credential management?",
            model=wiki_text,
        ))

    return examples


def build_strategy_examples(strategies_dir: Path) -> list[dict]:
    """Generate examples from strategy source code."""
    system = (
        "You are an expert Python developer specializing in quantitative trading "
        "strategies. Write clean, well-documented strategy modules that follow "
        "the mphinance patterns: class-based, inheriting from BaseStrategy, using "
        "yfinance for data and pandas for analysis."
    )

    examples = []

    for py_file in sorted(strategies_dir.glob("*.py")):
        if py_file.name == "__init__.py" or py_file.name == "base.py":
            continue

        code = read_file(py_file)
        if not code or len(code) < 200:
            continue

        strategy_name = py_file.stem.replace("_", " ").title()

        examples.append(make_example(
            system=system,
            user=f"Write a complete trading strategy module called '{strategy_name}' following the mphinance patterns. Include scanning logic, scoring, and proper documentation.",
            model=code,
        ))

    return examples


def build_pipeline_examples() -> list[dict]:
    """Generate examples from core pipeline modules."""
    system = (
        "You are an expert Python developer building a 13-stage quantitative "
        "trading pipeline. Write production-quality code with proper error "
        "handling, logging, and modular design."
    )

    examples = []
    pipeline_files = [
        ("dossier/charts.py", "Write a chart generator module using mplfinance with a dark HUD theme, Michael's EMA stack (8/21/34/55/89), and SMA 50/200 overlays."),
        ("dossier/momentum_picks.py", "Write a 9-factor ML-calibrated momentum scoring module. Include RSI, ADX, Stochastic, volume ratio, EMA alignment, and a Bounce 2.0 setup detector."),
        ("dossier/quality_filter.py", "Write a quality filter that scores tickers on data integrity. Check for SPACs, junk biotech, ETFs, ADRs, recent IPOs, and penny stocks."),
        ("dossier/persistence/tracker.py", "Write a signal persistence tracker with a 21-day rolling window. Classify tickers as Lifers (20+ days), High Conviction (10-19), or New Signals (1-3)."),
    ]

    for rel_path, prompt in pipeline_files:
        code = read_file(ROOT / rel_path)
        if code:
            examples.append(make_example(
                system=system,
                user=prompt,
                model=code,
            ))

    return examples


def main():
    parser = argparse.ArgumentParser(description="Prepare Vertex AI training dataset")
    parser.add_argument("--output", default="scripts/vertex_training_data.jsonl",
                        help="Output JSONL file path")
    parser.add_argument("--trigger-tuning", action="store_true",
                        help="Also trigger the Vertex AI tuning job")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print("═══ Vertex AI Dataset Preparation ═══\n")

    # Read source documents
    print("📚 Reading source documents...")
    voice_text = read_file(ROOT / "VOICE.md")
    claude_text = read_file(ROOT / "CLAUDE.md")
    wiki_text = read_file(ROOT / "WIKI.md")

    # Build training examples
    all_examples = []

    print("🎭 Building style examples (VOICE.md)...")
    style_examples = build_style_examples(voice_text)
    all_examples.extend(style_examples)
    print(f"  → {len(style_examples)} examples")

    print("🏗️ Building architecture examples (CLAUDE.md + WIKI.md)...")
    arch_examples = build_architecture_examples(claude_text, wiki_text)
    all_examples.extend(arch_examples)
    print(f"  → {len(arch_examples)} examples")

    print("📊 Building strategy examples (strategies/*.py)...")
    strat_examples = build_strategy_examples(ROOT / "strategies")
    all_examples.extend(strat_examples)
    print(f"  → {len(strat_examples)} examples")

    print("⚙️ Building pipeline examples (dossier/*.py)...")
    pipeline_examples = build_pipeline_examples()
    all_examples.extend(pipeline_examples)
    print(f"  → {len(pipeline_examples)} examples")

    # Write JSONL
    print(f"\n📝 Writing {len(all_examples)} examples to {output_path}...")
    with open(output_path, "w") as f:
        for example in all_examples:
            f.write(json.dumps(example) + "\n")

    file_size = output_path.stat().st_size
    print(f"  → {file_size:,} bytes")

    # Summary
    print(f"\n{'═' * 50}")
    print(f"  Total examples: {len(all_examples)}")
    print(f"  Style:          {len(style_examples)}")
    print(f"  Architecture:   {len(arch_examples)}")
    print(f"  Strategies:     {len(strat_examples)}")
    print(f"  Pipeline:       {len(pipeline_examples)}")
    print(f"{'═' * 50}")

    if args.trigger_tuning:
        trigger_vertex_tuning(output_path)
    else:
        print(f"\n💡 To trigger tuning, run:")
        print(f"   python {__file__} --trigger-tuning")
        print(f"\n   Or use gcloud CLI:")
        print(f"   1. Upload dataset: gsutil cp {output_path} gs://mphinance-pipeline-data/vertex/training_data.jsonl")
        print(f"   2. Start tuning job (see below)")


def trigger_vertex_tuning(dataset_path: Path):
    """Trigger a Vertex AI supervised fine-tuning job."""
    print("\n🚀 Triggering Vertex AI Tuning Job...\n")

    try:
        from google.cloud import aiplatform

        PROJECT_ID = "studio-3669937961-ea8a7"
        REGION = "us-central1"
        BUCKET = "mphinance-pipeline-data"

        aiplatform.init(project=PROJECT_ID, location=REGION)

        # Upload JSONL to GCS
        gcs_uri = f"gs://{BUCKET}/vertex/training_data.jsonl"
        print(f"  Uploading dataset to {gcs_uri}...")

        from google.cloud import storage
        client = storage.Client()
        bucket = client.bucket(BUCKET)
        blob = bucket.blob("vertex/training_data.jsonl")
        blob.upload_from_filename(str(dataset_path))
        print(f"  ✅ Uploaded ({dataset_path.stat().st_size:,} bytes)")

        # Create tuning job
        print(f"  Starting tuning job...")
        tuning_job = aiplatform.CustomJob.create(
            display_name="mphinance-style-tuning",
            # Use supervised tuning for Gemini
            # This creates a tuned adapter model
        )

        # Note: The actual Vertex AI tuning API for Gemini models uses
        # a different interface. Here's the gcloud equivalent:
        print(f"\n  ── Alternative: gcloud CLI ──")
        print(f"  gcloud ai tuning-jobs create \\")
        print(f"    --region={REGION} \\")
        print(f"    --source-model=gemini-1.5-flash-002 \\")
        print(f"    --training-dataset-uri={gcs_uri} \\")
        print(f"    --tuned-model-display-name=mphinance-sam-v1 \\")
        print(f"    --epoch-count=4 \\")
        print(f"    --learning-rate-multiplier=1.0")

    except ImportError:
        print("  [ERR] google-cloud-aiplatform not installed")
        print("  Install: pip install google-cloud-aiplatform")
    except Exception as e:
        print(f"  [ERR] {e}")
        print(f"\n  Fallback — use gcloud CLI:")
        print(f"  gsutil cp {dataset_path} gs://mphinance-pipeline-data/vertex/training_data.jsonl")
        print(f"  gcloud ai tuning-jobs create --region=us-central1 \\")
        print(f"    --source-model=gemini-1.5-flash-002 \\")
        print(f"    --training-dataset-uri=gs://mphinance-pipeline-data/vertex/training_data.jsonl \\")
        print(f"    --tuned-model-display-name=mphinance-sam-v1")


if __name__ == "__main__":
    main()
