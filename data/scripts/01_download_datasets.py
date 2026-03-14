"""
============================================================================
Script 01: Download Masakhane datasets for Ghomala' (bbj)
============================================================================
Downloads from HuggingFace:
  - MAFAND-MT: French ↔ Ghomala translation pairs (~2,000 pairs)
  - MasakhaNER2: Named Entity Recognition for Ghomala (~4,830 sentences)
  - MasakhaPOS: Part-of-Speech tagging for Ghomala (~1,300 sentences)

All datasets are open-source from the Masakhane NLP community.
Licenses: MAFAND-MT (CC-BY-4.0-NC), MasakhaNER2 (AFL-3.0), MasakhaPOS (CC-BY-4.0)

Usage:
  python 01_download_datasets.py

Output:
  data/raw/mafand_mt_fr_bbj.json
  data/raw/masakhaner2_bbj.json
  data/raw/masakhane_pos_bbj.json

Author: Daemon Craft Inc.
============================================================================
"""

import json
import os
from pathlib import Path

# ---------------------------------------------------------------------------
# NOTE: Run `pip install datasets` before first use
# ---------------------------------------------------------------------------
from datasets import load_dataset

# Output directory
RAW_DIR = Path(__file__).parent.parent / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)


def download_mafand_mt():
    """
    MAFAND-MT — Machine Translation dataset (French ↔ Ghomala')
    
    What it contains: Parallel sentences from news articles translated by 
    expert human translators into Ghomala'. Each entry has a French source 
    and a Ghomala' target.
    
    Format on HuggingFace:
      {"translation": {"src": "Le président...", "tgt": "Fə̀ mfɔ̀..."}}
    
    Why we need it: This is our PRIMARY dataset for teaching the model 
    to translate between French and Ghomala'.
    """
    print("\n📥 Downloading MAFAND-MT (French → Ghomala')...")
    
    # 'fr-bbj' = French to Ghomala (bbj = ISO 639-3 code for Ghomala')
    dataset = load_dataset("masakhane/mafand", "fr-bbj")
    
    all_entries = []
    total = 0
    for split_name in dataset:
        split_data = dataset[split_name]
        for item in split_data:
            entry = {
                "split": split_name,
                "french": item["translation"]["fr"],
                "ghomala": item["translation"]["bbj"]
            }
            all_entries.append(entry)
            total += 1
    
    output_path = RAW_DIR / "mafand_mt_fr_bbj.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Saved {total} translation pairs to {output_path}")
    
    # Show a sample so you can see the Ghomala' characters
    if all_entries:
        sample = all_entries[0]
        print(f"   📝 Sample:")
        print(f"      FR: {sample['french'][:80]}...")
        print(f"      BBJ: {sample['ghomala'][:80]}...")
    
    return all_entries


def download_masakhaner2():
    """
    MasakhaNER 2.0 — Named Entity Recognition for Ghomala'
    
    What it contains: Sentences annotated with entity types:
      PER (person), ORG (organization), LOC (location), DATE
    
    Format on HuggingFace:
      {"tokens": ["Wákàtí", "méje", ...], "ner_tags": [B-DATE, I-DATE, O, ...]}
    
    Why we need it: Helps the model understand Ghomala' sentence structure 
    and recognize important entities (names, places, dates).
    """
    print("\n📥 Downloading MasakhaNER 2.0 (Ghomala' NER)...")
    
    # 'bbj' = Ghomala subset
    dataset = load_dataset("masakhane/masakhaner2", "bbj")
    
    # NER tag mapping (from integer IDs to labels)
    ner_labels = ["O", "B-PER", "I-PER", "B-ORG", "I-ORG", "B-LOC", "I-LOC", "B-DATE", "I-DATE"]
    
    all_entries = []
    total = 0
    for split_name in dataset:
        split_data = dataset[split_name]
        for item in split_data:
            tokens = item["tokens"]
            tags = [ner_labels[t] if t < len(ner_labels) else "O" for t in item["ner_tags"]]
            
            entry = {
                "split": split_name,
                "sentence": " ".join(tokens),
                "tokens": tokens,
                "ner_tags": tags
            }
            all_entries.append(entry)
            total += 1
    
    output_path = RAW_DIR / "masakhaner2_bbj.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Saved {total} NER sentences to {output_path}")
    
    if all_entries:
        sample = all_entries[0]
        print(f"   📝 Sample sentence: {sample['sentence'][:80]}...")
    
    return all_entries


def download_masakhane_pos():
    """
    MasakhaPOS — Part-of-Speech tagging for Ghomala'
    
    What it contains: Sentences with grammatical tags for each word
      (NOUN, VERB, ADJ, ADV, etc.)
    
    Why we need it: Teaches the model Ghomala' grammar structure — 
    which words are nouns, verbs, etc. This helps generate grammatically 
    correct Ghomala' sentences.
    """
    print("\n📥 Downloading MasakhaPOS (Ghomala' POS tagging)...")
    
    try:
        dataset = load_dataset("masakhane/masakhane-pos", "bbj")
    except Exception:
        # Fallback: some versions use different naming
        try:
            dataset = load_dataset("masakhane/masakhapos", "bbj")
        except Exception as e:
            print(f"   ⚠️  Could not download MasakhaPOS: {e}")
            print("   ℹ️  This is optional. MAFAND-MT + MasakhaNER2 are sufficient.")
            return []
    
    all_entries = []
    total = 0
    for split_name in dataset:
        split_data = dataset[split_name]
        for item in split_data:
            tokens = item["tokens"]
            # POS tags are typically stored as integer IDs
            # Map them to UPOS labels
            upos_labels = [
                "ADJ", "ADP", "ADV", "AUX", "CCONJ", "DET", "INTJ",
                "NOUN", "NUM", "PART", "PRON", "PROPN", "PUNCT",
                "SCONJ", "SYM", "VERB", "X"
            ]
            tags = []
            for t in item.get("upos", item.get("pos_tags", [])):
                if isinstance(t, int) and t < len(upos_labels):
                    tags.append(upos_labels[t])
                else:
                    tags.append(str(t))
            
            entry = {
                "split": split_name,
                "sentence": " ".join(tokens),
                "tokens": tokens,
                "pos_tags": tags
            }
            all_entries.append(entry)
            total += 1
    
    output_path = RAW_DIR / "masakhane_pos_bbj.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_entries, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Saved {total} POS sentences to {output_path}")
    return all_entries


def print_summary(mafand, ner, pos):
    """Print a clear summary of all downloaded data."""
    print("\n" + "=" * 60)
    print("📊 DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"   MAFAND-MT (translation):  {len(mafand):>5} pairs")
    print(f"   MasakhaNER2 (NER):        {len(ner):>5} sentences")
    print(f"   MasakhaPOS (grammar):     {len(pos):>5} sentences")
    print(f"   {'─' * 40}")
    print(f"   TOTAL raw data:           {len(mafand) + len(ner) + len(pos):>5} entries")
    print(f"\n   📁 Files saved to: {RAW_DIR}")
    print(f"\n   ➡️  Next step: python 02_transform_to_jsonl.py")
    print("=" * 60)


if __name__ == "__main__":
    print("🌍 NAM SA' — Ghomala' Dataset Download Pipeline")
    print("=" * 60)
    
    mafand = download_mafand_mt()
    ner = download_masakhaner2()
    pos = download_masakhane_pos()
    
    print_summary(mafand, ner, pos)
