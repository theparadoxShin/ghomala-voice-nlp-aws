"""
============================================================================
Script 01: Download Ghomala' translation datasets
============================================================================
Downloads from HuggingFace:
  - stfotso/french-ghomala-bandjoun: French ↔ Ghomala' (~15,190 pairs)
    Source: Dictionnaire Ghomálá'-Français (Eichholzer, Domche-Teko, Mba, Nissim)
    License: Apache-2.0

  - stephanedonna/english_ghomala: English ↔ Ghomala' (~7,916 pairs)
    License: (see dataset card)

Also loads the local curated dictionary (ghomala_dictionary.json).

Usage:
  python 01_download_datasets.py

Output:
  data/raw/french_ghomala_bandjoun.json
  data/raw/english_ghomala.json
============================================================================
"""

import json
from pathlib import Path

# ---------------------------------------------------------------------------
# pip install datasets
# ---------------------------------------------------------------------------
from datasets import load_dataset

# Output directory
RAW_DIR = Path(__file__).parent.parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_french_ghomala():
    """
    stfotso/french-ghomala-bandjoun — French ↔ Ghomala' (Bandjoun dialect)

    What it contains: ~15,190 parallel pairs from the Dictionnaire Ghomálá'-Français
    edited by Erika Eichholzer with Prof. Dr. Engelbert Domche-Teko, Dr. Gabriel
    Mba and P. Gabriel Nissim. Includes words, expressions, and full sentences
    from biblical texts and news articles translated to Ghomala'.

    Columns: francais, ghomala
    """
    print("\nDownloading stfotso/french-ghomala-bandjoun...")

    dataset = load_dataset("stfotso/french-ghomala-bandjoun", split="train")

    all_entries = []
    for item in dataset:
        fr = (item.get("francais") or "").strip()
        bbj = (item.get("ghomala") or "").strip()
        if fr and bbj:
            all_entries.append({"french": fr, "ghomala": bbj})

    output_path = RAW_DIR / "french_ghomala_bandjoun.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"   ✅ Saved {len(all_entries)} French-Ghomala' pairs to {output_path}")

    if all_entries:
        s = all_entries[0]
        print(f"   Sample:")
        print(f"      FR:  {s['french'][:80]}")
        print(f"      BBJ: {s['ghomala'][:80]}")

    return all_entries


def download_english_ghomala():
    """
    stephanedonna/english_ghomala — English ↔ Ghomala'

    What it contains: ~7,916 parallel pairs of English text translated to
    Ghomala'. Primarily biblical and literary content.

    Columns: source (English), target (Ghomala')
    """
    print("\nDownloading stephanedonna/english_ghomala...")

    dataset = load_dataset("stephanedonna/english_ghomala", split="train")

    all_entries = []
    for item in dataset:
        en = (item.get("source") or "").strip()
        bbj = (item.get("target") or "").strip()
        if en and bbj:
            all_entries.append({"english": en, "ghomala": bbj})

    output_path = RAW_DIR / "english_ghomala.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)

    print(f"   ✅ Saved {len(all_entries)} English-Ghomala' pairs to {output_path}")

    if all_entries:
        s = all_entries[0]
        print(f"   Sample:")
        print(f"      EN:  {s['english'][:80]}")
        print(f"      BBJ: {s['ghomala'][:80]}")

    return all_entries


def print_summary(fr_data, en_data):
    """Print a clear summary of all downloaded data."""
    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"   French-Ghomala' (stfotso):     {len(fr_data):>6} pairs")
    print(f"   English-Ghomala' (stephanedonna): {len(en_data):>6} pairs")
    print(f"   {'─' * 45}")
    print(f"   TOTAL raw translation pairs:   {len(fr_data) + len(en_data):>6}")
    print(f"\n   Files saved to: {RAW_DIR}")
    print(f"\n   Next step: python 02_transform_to_jsonl.py")
    print("=" * 60)


if __name__ == "__main__":
    print("NAM SA' — Ghomala' Dataset Download Pipeline")
    print("=" * 60)

    fr_data = download_french_ghomala()
    en_data = download_english_ghomala()

    print_summary(fr_data, en_data)
