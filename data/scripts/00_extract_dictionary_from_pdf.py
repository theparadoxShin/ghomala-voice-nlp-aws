"""
============================================================================
Script 00: Extract Ghomala' dictionary from PDF using Gemini Vision AI
============================================================================
Converts each page of the Ghomala'-French dictionary PDF into clean,
properly Unicode-encoded JSON entries.

The original PDF uses a symbolic font that causes mojibake when
text is extracted directly. This script bypasses the text layer entirely
by sending page IMAGES to Gemini, which reads the glyphs visually and
outputs correct Unicode (ɔ, ɛ, ŋ, ə, tons, etc.).

Prerequisites:
  pip install google-genai PyMuPDF Pillow

Usage:
  python 00_extract_dictionary_from_pdf.py --pdf path/to/dictionary.pdf
  python 00_extract_dictionary_from_pdf.py --pdf dict.pdf --start-page 5
  python 00_extract_dictionary_from_pdf.py --pdf dict.pdf --start-page 10 --end-page 20

Environment:
  GEMINI_API_KEY  — Your Google AI Studio API key (https://aistudio.google.com/apikey)

Output:
  data/dictionary/ghomala_dictionary.json  (merged, deduplicated)
============================================================================
"""

import argparse
import io
import json
import os
import sys
import time
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("❌ PyMuPDF requis. Installe avec: pip install PyMuPDF")

try:
    from PIL import Image
except ImportError:
    sys.exit("❌ Pillow requis. Installe avec: pip install Pillow")

try:
    from google import genai
    from google.genai import types
except ImportError:
    sys.exit("❌ google-genai requis. Installe avec: pip install google-genai")

# ============================================================================
# PATHS
# ============================================================================
DICT_DIR = Path(__file__).parent.parent / "dictionary"
DICT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = DICT_DIR / "ghomala_dictionary.json"
PROGRESS_PATH = DICT_DIR / "extraction_progress.json"

# ============================================================================
# GEMINI PROMPTS — System instruction + User prompt (séparés)
# ============================================================================
SYSTEM_INSTRUCTION = """Tu es un linguiste expert en Ghomala' (Ghɔ̀málá'), langue Bamiléké du Cameroun.
Ta tâche est d'extraire les données d'un dictionnaire numérisé avec une précision absolue
sur l'orthographe, la phonétique et la grammaire Ghomala'.
Tu connais parfaitement l'Alphabet Général des Langues Camerounaises (AGLC).
"""

EXTRACTION_PROMPT = """Cette image est une page du "Dictionnaire Ghomálá'-Français" (Eichholzer, Domche-Teko, Mba, Nissim).
Extrais TOUTES les entrées de cette page.

Pour chaque entrée, remplis les 5 champs suivants:
- "ghomala": le mot ou expression en Ghomala' (avec tons et caractères spéciaux)
- "french": la traduction française
- "category": la catégorie grammaticale (N., V., Adj., Adv., Pron., Part., Conj., N1/2., N1/4., N3., N3/4., Vt., Vi., Vrefl., etc.)
- "example": la phrase d'exemple en Ghomala' + traduction française ("" si absente)
- "cultural_note": les notes (Dom.Sém.:, Syn.:, Var.:, Pl.:, Empr.de:, Cf.:, etc.) ("" si absentes)

RÈGLES CRITIQUES pour le Ghomala':
1. Utilise les vrais caractères Unicode: ɔ (U+0254), ɛ (U+025B), ŋ (U+014B), ə (U+0259), ʉ (U+0289)
2. Marque les tons: à (grave), á (aigu), â (circonflexe), ǎ (caron/montant)
3. Les tons s'appliquent aussi aux caractères spéciaux: ɔ́, ɔ̀, ɔ̂, ɛ́, ɛ̀, ə̀, ə́
4. Utilise l'apostrophe droite ' pour la glottale
5. Sépare les sens avec "1) ... 2) ..."
6. Si homonymes, ajoute un indice (ex: mot₁, mot₂)
"""


# Schema for structured output
ENTRY_SCHEMA = types.Schema(
    type="ARRAY",
    items=types.Schema(
        type="OBJECT",
        properties={
            "ghomala": types.Schema(type="STRING", description="Mot en Ghomala' avec tons"),
            "french": types.Schema(type="STRING", description="Traduction française"),
            "category": types.Schema(type="STRING", description="Catégorie grammaticale"),
            "example": types.Schema(type="STRING", description="Phrase d'exemple"),
            "cultural_note": types.Schema(type="STRING", description="Notes culturelles"),
        },
        required=["ghomala", "french"],
    ),
)


def setup_gemini(api_key: str):
    """Configure le client Gemini avec la clé API."""
    client = genai.Client(api_key=api_key)
    return client


def pdf_page_to_image(pdf_path: str, page_num: int, dpi: int = 250) -> Image.Image:
    """Convert a single PDF page to a PIL Image at the given DPI."""
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    # Higher DPI = clearer text for OCR
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return Image.open(io.BytesIO(img_bytes))


def extract_json_from_response(text: str) -> list:
    """Parse le JSON de la réponse Gemini (mode structured output)."""
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            # Gemini peut envelopper dans une clé comme {"entries": [...]}
            for value in data.values():
                if isinstance(value, list):
                    return value
            return [data]
        return []
    except json.JSONDecodeError as e:
        print(f"      JSON parse error: {e}")
        return []


def load_existing_entries() -> list:
    """Load already extracted entries from the output file."""
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_progress() -> dict:
    """Load extraction progress (which pages are done)."""
    if PROGRESS_PATH.exists():
        with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"completed_pages": [], "total_entries": 0}


def save_progress(progress: dict):
    """Save extraction progress."""
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump(progress, f, indent=2)


def save_entries(entries: list):
    """Save all entries to the output JSON file, deduplicated."""
    # Deduplicate by (ghomala, french) pair
    seen = set()
    unique = []
    for entry in entries:
        key = (entry.get("ghomala", ""), entry.get("french", ""))
        if key not in seen:
            seen.add(key)
            unique.append(entry)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    return unique


def validate_entry(entry: dict) -> bool:
    """Basic validation: must have ghomala and french fields."""
    ghomala = entry.get("ghomala", "").strip()
    french = entry.get("french", "").strip()
    return bool(ghomala and french)


def extract_page(client, pdf_path: str, page_num: int, max_retries: int = 3) -> list:
    """Extract dictionary entries from a single PDF page."""
    img = pdf_page_to_image(pdf_path, page_num)

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[EXTRACTION_PROMPT, img],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    temperature=0.1,
                    top_p=0.95,
                    max_output_tokens=65536,
                    response_mime_type="application/json",
                    response_schema=ENTRY_SCHEMA,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                    http_options=types.HttpOptions(timeout=120_000),
                ),
            )
            entries = extract_json_from_response(response.text)
            valid = [e for e in entries if validate_entry(e)]

            if valid:
                return valid

            if attempt < max_retries - 1:
                print(f"      No valid entries, retrying ({attempt + 2}/{max_retries})...")
                time.sleep(2)

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                wait = 30 * (attempt + 1)
                print(f"      Rate limited, waiting {wait}s...")
                time.sleep(wait)
            elif attempt < max_retries - 1:
                print(f"      Retrying: {error_msg[:100]}...")
                time.sleep(5)
            else:
                print(f"      ❌ Failed after {max_retries} attempts: {error_msg[:100]}")

    return []


def main():
    parser = argparse.ArgumentParser(
        description="Extract Ghomala' dictionary from PDF using Gemini Vision AI",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--pdf", type=str, required=True, help="Path to the dictionary PDF file"
    )
    parser.add_argument(
        "--start-page",
        type=int,
        default=0,
        help="First page to extract (0-indexed, default: 0)",
    )
    parser.add_argument(
        "--end-page",
        type=int,
        default=None,
        help="Last page to extract (inclusive). Default: last page",
    )
    parser.add_argument(
        "--dpi",
        type=int,
        default=250,
        help="Image resolution for page rendering (default: 250)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=4.0,
        help="Seconds to wait between API calls (default: 4.0)",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last extraction progress (skip completed pages)",
    )

    args = parser.parse_args()

    # ---------------------------------------------------------------------------
    # API key
    # ---------------------------------------------------------------------------
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        sys.exit(
            "❌ GEMINI_API_KEY non définie.\n"
            "   → Va sur https://aistudio.google.com/apikey\n"
            "   → Crée une clé API\n"
            "   → $env:GEMINI_API_KEY = 'ta-clé-ici'"
        )

    # ---------------------------------------------------------------------------
    # PDF info
    # ---------------------------------------------------------------------------
    pdf_path = args.pdf
    if not os.path.exists(pdf_path):
        sys.exit(f"❌ Fichier PDF introuvable: {pdf_path}")

    doc = fitz.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    start = args.start_page
    end = args.end_page if args.end_page is not None else total_pages - 1
    end = min(end, total_pages - 1)

    print("NAM SA' — Extraction du Dictionnaire Ghomala'")
    print("=" * 60)
    print(f"   PDF: {pdf_path} ({total_pages} pages)")
    print(f"   Pages a traiter: {start} -> {end} ({end - start + 1} pages)")
    print(f"   Gemini API: ...{api_key[-8:]}")
    print(f"   Delai entre pages: {args.delay}s")
    print("=" * 60)

    # ---------------------------------------------------------------------------
    # Setup
    # ---------------------------------------------------------------------------
    client = setup_gemini(api_key)
    all_entries = load_existing_entries()
    progress = load_progress() if args.resume else {"completed_pages": [], "total_entries": 0}

    initial_count = len(all_entries)
    print(f"\n   Entrees existantes: {initial_count}")

    # ---------------------------------------------------------------------------
    # Extract page by page
    # ---------------------------------------------------------------------------
    pages_to_process = []
    for p in range(start, end + 1):
        if args.resume and p in progress["completed_pages"]:
            continue
        pages_to_process.append(p)

    if not pages_to_process:
        print("\n   ✅ Toutes les pages demandées sont déjà extraites!")
        return

    print(f"   Pages a extraire: {len(pages_to_process)}")
    print()

    for idx, page_num in enumerate(pages_to_process):
        print(f"   [{idx + 1}/{len(pages_to_process)}] Page {page_num}...", end=" ", flush=True)

        entries = extract_page(client, pdf_path, page_num)

        if entries:
            all_entries.extend(entries)
            progress["completed_pages"].append(page_num)
            progress["total_entries"] = len(all_entries)
            print(f"✅ {len(entries)} entrées")
        else:
            print("⚠️  0 entrées (page vide ou erreur)")

        # Save after each page (resume-safe)
        unique_entries = save_entries(all_entries)
        all_entries = unique_entries
        save_progress(progress)

        # Rate limiting
        if idx < len(pages_to_process) - 1:
            time.sleep(args.delay)

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    final_count = len(all_entries)
    new_count = final_count - initial_count

    print("\n" + "=" * 60)
    print("RESULTAT DE L'EXTRACTION")
    print("=" * 60)
    print(f"   Entrees avant extraction:     {initial_count:>6}")
    print(f"   Nouvelles entrees:            {new_count:>6}")
    print(f"   Total (deduplique):           {final_count:>6}")
    print(f"\n   Fichier: {OUTPUT_PATH}")
    print(f"   Progres: {PROGRESS_PATH}")

    # Check Unicode quality
    unicode_chars = set()
    for entry in all_entries:
        for char in entry.get("ghomala", ""):
            if ord(char) > 127:
                unicode_chars.add(char)

    expected = {"ɔ", "ɛ", "ŋ", "ə", "ʉ"}
    found = expected & unicode_chars
    print(f"\n   Caracteres Unicode Ghomala' trouves: {', '.join(sorted(found))}")
    if found == expected:
        print("   ✅ Tous les caractères spéciaux sont présents!")
    else:
        missing = expected - found
        print(f"   ⚠️  Manquants: {', '.join(sorted(missing))}")

    print(f"\n   Prochaine etape: python 01_download_datasets.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
