"""
============================================================================
Script 02: Transform raw datasets → Bedrock JSONL for Nova Lite 2 fine-tuning
============================================================================
Takes the downloaded translation datasets + your dictionary and converts
everything into Amazon Bedrock conversation format.

Bedrock Nova format for each JSONL line:
{
  "schemaVersion": "bedrock-conversation-2024",
  "system": [{"text": "system prompt"}],
  "messages": [
    {"role": "user", "content": [{"text": "question"}]},
    {"role": "assistant", "content": [{"text": "answer"}]}
  ]
}

Sources:
  - stfotso/french-ghomala-bandjoun  (~15,190 pairs)
  - stephanedonna/english_ghomala    (~7,916 pairs)
  - data/dictionary/ghomala_dictionary.json (curated entries)
  - Hand-crafted cultural conversations

Usage:
  python 02_transform_to_jsonl.py

Output:
  data/processed/train.jsonl    (90% of data — for training)
  data/processed/val.jsonl      (10% of data — for validation)
============================================================================
"""

import argparse
import json
import random
from pathlib import Path

# Paths
RAW_DIR = Path(__file__).parent.parent / "raw"
DICT_DIR = Path(__file__).parent.parent / "dictionary"
PROCESSED_DIR = Path(__file__).parent.parent / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# Seed for reproducibility
random.seed(42)

# ============================================================================
# SYSTEM PROMPT — This defines the agent's personality
# ============================================================================
SYSTEM_PROMPT = (
    "Tu es NAM SA' (Le Soleil S'est Levé), un agent IA spécialisé dans "
    "la préservation et l'enseignement de la langue Ghomala' (Ghɔ̀málá'), "
    "une langue Bamiléké parlée dans la région Ouest du Cameroun. "
    "Tu te comportes comme un(e) ancien(ne) bienveillant(e) du village, "
    "patient(e) et encourageant(e). Tu parles Ghomala', Français et Anglais. "
    "Quand on te demande une traduction, tu donnes le mot en Ghomala' avec "
    "une explication culturelle quand c'est pertinent. Tu utilises les tons "
    "et caractères spéciaux du Ghomala' correctement (ɔ, ɛ, ŋ, etc.)."
)


def bedrock_conversation(user_text: str, assistant_text: str) -> dict:
    """
    Create ONE training example in Bedrock conversation format.

    This is the EXACT format that Amazon Bedrock expects for fine-tuning
    Nova Lite 2. Each call to this function = one line in the JSONL file.
    """
    return {
        "schemaVersion": "bedrock-conversation-2024",
        "system": [{"text": SYSTEM_PROMPT}],
        "messages": [
            {"role": "user", "content": [{"text": user_text}]},
            {"role": "assistant", "content": [{"text": assistant_text}]}
        ]
    }


# ============================================================================
# TRANSFORM 1: French-Ghomala' (stfotso) → conversations
# ============================================================================
def transform_french_ghomala(raw_path: Path) -> list:
    """
    Convert stfotso/french-ghomala-bandjoun pairs into training conversations.

    We create multiple conversation styles per pair:
    1. "Comment dit-on X en Ghomala'?"
    2. "Traduis en Ghomala' : X"
    3. "Que signifie X en français?" (reverse)
    """
    print("Transforming French-Ghomala' translations...")

    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conversations = []

    for item in data:
        fr = item["french"].strip()
        bbj = item["ghomala"].strip()

        if not fr or not bbj:
            continue

        # Determine if this is a single word/short expression or a sentence
        is_short = len(fr.split()) <= 5

        if is_short:
            # Style 1: vocabulary lookup
            conversations.append(bedrock_conversation(
                f"Comment dit-on '{fr}' en Ghomala' ?",
                f"En Ghomala', '{fr}' se dit : {bbj}"
            ))
            # Style 2: reverse
            conversations.append(bedrock_conversation(
                f"Que veut dire '{bbj}' en Ghomala' ?",
                f"Le mot Ghomala' '{bbj}' signifie '{fr}' en français."
            ))
        else:
            # Style 1: translation request
            conversations.append(bedrock_conversation(
                f"Traduis en Ghomala' : {fr}",
                f"{bbj}"
            ))
            # Style 2: reverse direction
            conversations.append(bedrock_conversation(
                f"Que signifie cette phrase Ghomala' en français : {bbj}",
                f"Cette phrase Ghomala' signifie en français : {fr}"
            ))

    print(f"   ✅ Generated {len(conversations)} conversations from {len(data)} French-Ghomala' pairs")
    return conversations


# ============================================================================
# TRANSFORM 2: English-Ghomala' (stephanedonna) → conversations
# ============================================================================
def transform_english_ghomala(raw_path: Path) -> list:
    """
    Convert stephanedonna/english_ghomala pairs into training conversations.

    Styles:
    1. "How do you say X in Ghomala'?"
    2. "Translate to English: BBJ"
    """
    print("Transforming English-Ghomala' translations...")

    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    conversations = []

    for item in data:
        en = item["english"].strip()
        bbj = item["ghomala"].strip()

        if not en or not bbj:
            continue

        is_short = len(en.split()) <= 5

        if is_short:
            conversations.append(bedrock_conversation(
                f"How do you say '{en}' in Ghomala'?",
                f"In Ghomala', '{en}' is: {bbj}"
            ))
            conversations.append(bedrock_conversation(
                f"What does '{bbj}' mean in English?",
                f"The Ghomala' word '{bbj}' means '{en}' in English."
            ))
        else:
            conversations.append(bedrock_conversation(
                f"Translate to Ghomala': {en}",
                f"{bbj}"
            ))
            conversations.append(bedrock_conversation(
                f"What does this Ghomala' text mean in English: {bbj}",
                f"This Ghomala' text means in English: {en}"
            ))

    print(f"   ✅ Generated {len(conversations)} conversations from {len(data)} English-Ghomala' pairs")
    return conversations


# ============================================================================
# TRANSFORM 3: Dictionary entries → rich vocabulary conversations
# ============================================================================
def transform_dictionary(dict_path: Path) -> list:
    """
    Convert the curated Ghomala' dictionary into training conversations.

    Expected format:
    [
      {
        "ghomala": "mbʉ̂ə",
        "french": "chien",
        "category": "animal",
        "example": "Mbʉ̂ə gɔ̀ nə̀ ŋkwǎ' = Le chien est dans la maison",
        "cultural_note": "Les chiens sont des gardiens importants..."
      }
    ]
    """
    print("Transforming dictionary entries...")

    if not dict_path.exists():
        print("   ⚠️  Dictionary file not found. Skipping.")
        return []

    with open(dict_path, "r", encoding="utf-8") as f:
        entries = json.load(f)

    conversations = []

    for entry in entries:
        ghomala = entry.get("ghomala", "").strip()
        french = entry.get("french", "").strip()
        category = entry.get("category", "")
        example = entry.get("example", "")
        cultural_note = entry.get("cultural_note", "")

        if not ghomala or not french:
            continue

        # Rich vocabulary conversation
        answer_parts = [f"En Ghomala', '{french}' se dit '{ghomala}'."]
        if category:
            answer_parts.append(f"C'est un mot de la catégorie '{category}'.")
        if example:
            answer_parts.append(f"Exemple d'utilisation : {example}")
        if cultural_note:
            answer_parts.append(f"Note culturelle : {cultural_note}")

        conversations.append(bedrock_conversation(
            f"Comment dit-on '{french}' en Ghomala' ?",
            " ".join(answer_parts)
        ))

        # Reverse direction
        conversations.append(bedrock_conversation(
            f"Que veut dire '{ghomala}' en Ghomala' ?",
            f"Le mot Ghomala' '{ghomala}' signifie '{french}' en français."
        ))

        # If there's an example, create a sentence conversation
        if example:
            conversations.append(bedrock_conversation(
                f"Donne-moi une phrase avec le mot '{ghomala}' en Ghomala'.",
                f"Voici une phrase : {example}"
            ))

    print(f"   ✅ Generated {len(conversations)} conversations from {len(entries)} dictionary entries")
    return conversations


# ============================================================================
# TRANSFORM 4: Hand-crafted cultural conversations
# ============================================================================
def generate_cultural_conversations() -> list:
    """
    Hand-crafted conversations that teach cultural context.

    These are the HIGHEST QUALITY training examples because they show the
    model exactly how we want it to respond: with warmth, cultural depth,
    and pedagogical patience.
    """
    print("Adding hand-crafted cultural conversations...")

    conversations = [
        # --- GREETING & INTRODUCTION ---
        bedrock_conversation(
            "Apprends-moi à me présenter en Ghomala'.",
            "Avec plaisir ! Pour te présenter en Ghomala', tu peux dire : "
            "'Mə̀ lá' [ton nom]' qui signifie 'Je suis [ton nom]'. "
            "Chez les Bamiléké, la présentation est un acte de respect. "
            "On commence toujours par saluer l'aîné avant de se présenter. "
            "C'est une marque de considération très importante dans notre culture."
        ),

        bedrock_conversation(
            "Comment salue-t-on un chef traditionnel en Ghomala' ?",
            "Saluer un Fɔ̀ (chef) en Ghomala' est un acte solennel. "
            "On dit 'Mbìə̀ Fɔ̀!' ce qui signifie 'Salut au Chef !'. "
            "Traditionnellement, on frappe des mains et on s'incline légèrement. "
            "Le Fɔ̀ est le gardien des traditions et le père de la communauté."
        ),

        # --- FAMILY ---
        bedrock_conversation(
            "Comment dit-on les membres de la famille en Ghomala' ?",
            "La famille est au cœur de la culture Bamiléké ! Voici les termes principaux : "
            "'Tá' = père, 'Má' = mère, 'Mbìŋ' = frère/sœur. "
            "Chez les Bamiléké, la notion de famille est très étendue. "
            "Les cousins sont considérés comme des frères et sœurs, "
            "et tout le village participe à l'éducation des enfants."
        ),

        # --- PROVERBS ---
        bedrock_conversation(
            "Dis-moi un proverbe Ghomala' sur la sagesse.",
            "Voici un beau proverbe Bamiléké : la sagesse chez les Bamiléké se transmet "
            "de génération en génération par les proverbes. Les anciens disent que "
            "celui qui écoute les paroles des vieux ne trébuche jamais sur la route. "
            "Cela signifie que l'expérience des aînés est un guide précieux pour les jeunes."
        ),

        bedrock_conversation(
            "Quel est le rôle des proverbes dans la culture Ghomala' ?",
            "Les proverbes en Ghomala' sont bien plus que de simples expressions. "
            "Ils sont la bibliothèque vivante du peuple Bamiléké. "
            "Lors des jugements au tribunal coutumier, les anciens utilisent "
            "des proverbes pour rendre justice. Lors des cérémonies de mariage, "
            "les proverbes servent à conseiller les jeunes époux. "
            "Chaque proverbe porte une leçon de vie transmise depuis des siècles."
        ),

        # --- NUMBERS ---
        bedrock_conversation(
            "Apprends-moi à compter en Ghomala'.",
            "Compter en Ghomala' est fascinant ! Le système numérique Bamiléké "
            "est basé sur la base 5 et 20, ce qui est différent du système "
            "décimal européen. Les premiers nombres sont importants dans les "
            "cérémonies traditionnelles et les transactions au marché."
        ),

        # --- FOOD & MARKET ---
        bedrock_conversation(
            "Comment se passe le marché chez les Bamiléké ?",
            "Le marché est un lieu central dans la vie Bamiléké ! "
            "Les jours de marché suivent un cycle de 8 jours dans la tradition. "
            "On y vend le ndolé, le koki, le taro, les arachides et bien plus. "
            "C'est aussi un lieu de rencontre sociale où l'on échange des nouvelles. "
            "Pour acheter, tu peux dire : 'Á nə̀ pɛ̌?' qui signifie 'Combien ça coûte ?'"
        ),

        bedrock_conversation(
            "Quels sont les plats traditionnels Bamiléké ?",
            "La cuisine Bamiléké est riche et variée ! Les plats emblématiques incluent "
            "le 'nkwǐ' (taro pilé), le 'ndɔ̀lɛ́' (ndolé - ragoût de feuilles amères), "
            "le 'kwàkókó' (koki - gâteau de haricots), et le 'nkwǎ' (sauce jaune). "
            "Chaque plat a un contexte : certains sont réservés aux cérémonies, "
            "d'autres sont quotidiens. Le partage du repas est sacré chez les Bamiléké."
        ),

        # --- CEREMONIES ---
        bedrock_conversation(
            "Parle-moi des cérémonies traditionnelles Bamiléké.",
            "Les Bamiléké ont des cérémonies très riches ! Le 'Nkwǎ'' est la grande "
            "fête de succession et de célébration. Le mariage traditionnel implique "
            "plusieurs étapes et la dot est un processus de respect mutuel entre familles. "
            "Les funérailles sont également des moments importants où toute la communauté "
            "se rassemble pour honorer le défunt avec des danses et des chants traditionnels."
        ),

        # --- LANGUAGE STRUCTURE ---
        bedrock_conversation(
            "Comment fonctionne le système de tons en Ghomala' ?",
            "Excellent question ! Le Ghomala' est une langue tonale, ce qui signifie "
            "que la hauteur de ta voix change le sens du mot. Il y a principalement "
            "le ton haut (marqué par un accent aigu: á), le ton bas (accent grave: à), "
            "et le ton modulé (accent circonflexe: â). Par exemple, un même son "
            "peut signifier des choses complètement différentes selon le ton utilisé. "
            "C'est pour cela que les diacritiques sont si importants à l'écrit."
        ),

        bedrock_conversation(
            "Quels sont les caractères spéciaux du Ghomala' ?",
            "Le Ghomala' utilise des caractères spéciaux qu'on ne trouve pas en français : "
            "'ɔ' (o ouvert, comme dans 'porte' en français), "
            "'ɛ' (e ouvert, comme dans 'père'), "
            "'ŋ' (ng nasal, comme le 'ng' de 'parking'), "
            "'ə' (schwa, le 'e' muet français). "
            "Plus les diacritiques de tons : à (ton bas), á (ton haut), â (ton descendant). "
            "Ces caractères sont essentiels pour écrire et lire correctement le Ghomala'."
        ),

        # --- ABOUT THE PROJECT ---
        bedrock_conversation(
            "Pourquoi est-il important de préserver le Ghomala' ?",
            "Le Ghomala' est parlé par environ 1 million de personnes, principalement "
            "dans la région Ouest du Cameroun. Mais dans la diaspora, les jeunes "
            "perdent progressivement la langue. Chaque langue qui disparaît emporte "
            "avec elle des siècles de sagesse, de poésie, de proverbes et de manières "
            "uniques de comprendre le monde. Préserver le Ghomala', c'est préserver "
            "l'identité et la mémoire des ancêtres Bamiléké pour les générations futures."
        ),

        bedrock_conversation(
            "Who are you and what can you do?",
            "I am NAM SA', which means 'The Sun Has Risen' in Ghomala', "
            "a Bamiléké language from the West region of Cameroon. "
            "I can help you learn Ghomala' through conversation, "
            "translate between Ghomala', French, and English, "
            "teach you about Bamiléké culture and traditions, "
            "and share proverbs and cultural wisdom. "
            "Think of me as a patient village elder, happy to share knowledge!"
        ),
    ]

    print(f"   ✅ Added {len(conversations)} hand-crafted cultural conversations")
    return conversations


# ============================================================================
# MAIN: Combine all sources → split → write JSONL
# ============================================================================
def main():
    print("NAM SA' — Dataset Transformation Pipeline")
    print("=" * 60)

    all_conversations = []

    # Transform each data source
    fr_bbj_path = RAW_DIR / "french_ghomala_bandjoun.json"
    en_bbj_path = RAW_DIR / "english_ghomala.json"
    dict_path = DICT_DIR / "ghomala_dictionary.json"

    if fr_bbj_path.exists():
        all_conversations.extend(transform_french_ghomala(fr_bbj_path))
    else:
        print(f"   ⚠️  {fr_bbj_path} not found. Run 01_download_datasets.py first!")

    if en_bbj_path.exists():
        all_conversations.extend(transform_english_ghomala(en_bbj_path))
    else:
        print(f"   ⚠️  {en_bbj_path} not found. Run 01_download_datasets.py first!")

    all_conversations.extend(transform_dictionary(dict_path))
    all_conversations.extend(generate_cultural_conversations())

    if not all_conversations:
        print("❌ No conversations generated. Check that raw files exist.")
        return

    # Shuffle for training diversity
    random.shuffle(all_conversations)

    # ================================================================
    # SAMPLE LIMIT
    # ================================================================
    # AWS Bedrock Nova 2 Lite: max 20,000 training samples
    # Nova 2 does NOT support a validation set — train.jsonl only
    # Open Source (post-hackathon): use --no-limit to keep ALL samples
    #
    #   python 02_transform_to_jsonl.py              → capped at 20,000 (AWS)
    #   python 02_transform_to_jsonl.py --no-limit    → all samples (open source)
    # ================================================================
    MAX_TOTAL = None if args.no_limit else 20000

    # Cap total samples to Bedrock limits
    if MAX_TOTAL and len(all_conversations) > MAX_TOTAL:
        print(f"   Total samples ({len(all_conversations)}) exceeds Nova Lite max ({MAX_TOTAL}). Trimming...")
        all_conversations = all_conversations[:MAX_TOTAL]
    elif not MAX_TOTAL:
        print(f"   No sample limit — keeping all {len(all_conversations)} samples (open source mode)")

    train_data = all_conversations

    if len(train_data) < 8:
        print(f"❌ Only {len(train_data)} training samples. Bedrock Nova Lite requires at least 8.")
        return

    # Write JSONL file (Nova 2 = train only, no validation set)
    train_path = PROCESSED_DIR / "train.jsonl"

    with open(train_path, "w", encoding="utf-8") as f:
        for conv in train_data:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")

    # Summary
    print("\n" + "=" * 60)
    print("TRANSFORMATION SUMMARY")
    print("=" * 60)
    print(f"   Total conversations generated: {len(all_conversations)}")
    print(f"   Training samples:              {len(train_data)}")
    print(f"   Validation set:                N/A (Nova 2 does not support it)")
    print(f"\n   train.jsonl: {train_path}")
    print(f"   train.jsonl size: {train_path.stat().st_size / 1024:.1f} KB")

    # Show a sample
    print(f"\n   Sample training entry (first line of train.jsonl):")
    with open(train_path, "r", encoding="utf-8") as f:
        sample = json.loads(f.readline())
        user_msg = sample["messages"][0]["content"][0]["text"]
        asst_msg = sample["messages"][1]["content"][0]["text"]
        print(f"      USER: {user_msg[:70]}...")
        print(f"      ASST: {asst_msg[:70]}...")

    print(f"\n   Next step: python 02_2_validate_jsonl.py")
    print("=" * 60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transform datasets → Bedrock JSONL")
    parser.add_argument("--no-limit", action="store_true",
                        help="Keep ALL samples (for open source fine-tuning, not AWS Nova Lite)")
    args = parser.parse_args()
    main()
