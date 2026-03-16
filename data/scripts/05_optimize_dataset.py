"""
============================================================================
Script 05: Optimize dataset for fast fine-tuning iteration
============================================================================
Selects a balanced subset from the full train.jsonl for quick fine-tuning.
Prioritizes diversity: cultural conversations, dictionary, FR-BBJ, EN-BBJ.

Usage:
  python 05_optimize_dataset.py --samples 2000
  python 05_optimize_dataset.py --samples 2000 --output data/processed/train_v1.jsonl

Output:
  data/processed/train_v1.jsonl  (optimized subset)
============================================================================
"""

import argparse
import json
import random
from pathlib import Path

random.seed(42)

def classify_sample(sample: dict) -> str:
    """Classify a training sample by its source/type."""
    user_text = sample["messages"][0]["content"][0]["text"]
    assistant_text = sample["messages"][1]["content"][0]["text"]

    # Hand-crafted cultural (longest, richest answers)
    if len(assistant_text) > 300:
        return "cultural"

    # Dictionary entries (have "catégorie" or "Note culturelle")
    if "catégorie" in assistant_text or "Note culturelle" in assistant_text:
        return "dictionary"

    # English pairs
    if any(kw in user_text for kw in ["How do you say", "Translate to Ghomala'", "mean in English"]):
        return "english"

    # French pairs (default)
    return "french"


def main():
    parser = argparse.ArgumentParser(description="Optimize dataset for fast fine-tuning")
    parser.add_argument("--input", type=str, default="train_original.jsonl",
                        help="Path to full training JSONL")
    parser.add_argument("--output", type=str, default="data/processed/train_v1.jsonl",
                        help="Path for optimized output")
    parser.add_argument("--samples", type=int, default=2000,
                        help="Target number of samples")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load all samples
    print(f"Loading {input_path}...")
    with open(input_path, "r", encoding="utf-8") as f:
        all_samples = [json.loads(line) for line in f if line.strip()]
    print(f"  Total samples: {len(all_samples)}")

    # Classify
    buckets = {"cultural": [], "dictionary": [], "english": [], "french": []}
    for sample in all_samples:
        category = classify_sample(sample)
        buckets[category].append(sample)

    print("\nDistribution in full dataset:")
    for cat, items in buckets.items():
        print(f"  {cat}: {len(items)}")

    # Allocation strategy: prioritize quality
    #  - ALL cultural (hand-crafted, highest quality)
    #  - Proportional from dictionary, english, french
    target = args.samples
    selected = []

    # 1. Take ALL cultural conversations (they're few and highest quality)
    selected.extend(buckets["cultural"])
    remaining = target - len(selected)
    print(f"\nSelected {len(buckets['cultural'])} cultural conversations (all)")

    # 2. Take a good chunk of dictionary (high quality)
    dict_count = min(len(buckets["dictionary"]), remaining // 3)
    random.shuffle(buckets["dictionary"])
    selected.extend(buckets["dictionary"][:dict_count])
    remaining = target - len(selected)
    print(f"Selected {dict_count} dictionary entries")

    # 3. Split remaining 50/50 between french and english
    fr_count = min(len(buckets["french"]), remaining // 2)
    en_count = min(len(buckets["english"]), remaining - fr_count)

    random.shuffle(buckets["french"])
    random.shuffle(buckets["english"])
    selected.extend(buckets["french"][:fr_count])
    selected.extend(buckets["english"][:en_count])
    print(f"Selected {fr_count} French-Ghomala' pairs")
    print(f"Selected {en_count} English-Ghomala' pairs")

    # Shuffle final selection
    random.shuffle(selected)

    # Write output
    with open(output_path, "w", encoding="utf-8") as f:
        for sample in selected:
            f.write(json.dumps(sample, ensure_ascii=False) + "\n")

    size_kb = output_path.stat().st_size / 1024
    print(f"\n{'='*60}")
    print(f"OPTIMIZED DATASET READY")
    print(f"{'='*60}")
    print(f"  Samples: {len(selected)}")
    print(f"  File:    {output_path}")
    print(f"  Size:    {size_kb:.1f} KB")
    print(f"\nNext: upload to S3 and launch fine-tuning")


if __name__ == "__main__":
    main()
