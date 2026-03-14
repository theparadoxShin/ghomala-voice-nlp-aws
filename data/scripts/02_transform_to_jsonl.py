"""
============================================================================
Script 02: Transform raw datasets → Bedrock JSONL for fine-tuning
============================================================================
Takes the raw Masakhane data + your dictionary and converts everything 
into the Amazon Bedrock conversation format (bedrock-conversation-2024).

What is JSONL?
  - A text file where EACH LINE is one complete JSON object
  - Each line = one training example (one conversation)
  - Bedrock reads it line by line to train the model
  - Unlike regular JSON (one big array), JSONL is streamable

Bedrock format for each line:
{
  "schemaVersion": "bedrock-conversation-2024",
  "system": [{"text": "system prompt"}],
  "messages": [
    {"role": "user", "content": [{"text": "question"}]},
    {"role": "assistant", "content": [{"text": "answer"}]}
  ]
}

Usage:
  python 02_transform_to_jsonl.py

Output:
  data/processed/train.jsonl    (90% of data — for training)
  data/processed/val.jsonl      (10% of data — for validation)

Author: Daemon Craft Inc.
============================================================================
"""

import json
import random
import os
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
    Nova 2 Lite. Each call to this function = one line in the JSONL file.
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
# TRANSFORM 1: MAFAND-MT translation pairs → conversations
# ============================================================================
def transform_mafand(raw_path: Path) -> list:
    """
    Convert translation pairs into conversational training examples.
    
    From: {"french": "Le président...", "ghomala": "Fə̀ mfɔ̀..."}
    To: User asks → Assistant translates with cultural context
    
    We create MULTIPLE conversation styles per pair to increase diversity:
    1. "Comment dit-on X en Ghomala'?"
    2. "Traduis cette phrase en Ghomala': X"  
    3. "Que signifie X en français?" (reverse direction)
    """
    print("🔄 Transforming MAFAND-MT translations...")
    
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    conversations = []
    
    for item in data:
        fr = item["french"].strip()
        bbj = item["ghomala"].strip()
        
        if not fr or not bbj:
            continue
        
        # Style 1: French → Ghomala' translation request
        conversations.append(bedrock_conversation(
            f"Comment dit-on en Ghomala' : {fr}",
            f"En Ghomala', on dit : {bbj}"
        ))
        
        # Style 2: Direct translation command
        conversations.append(bedrock_conversation(
            f"Traduis en Ghomala' : {fr}",
            f"{bbj}"
        ))
        
        # Style 3: Ghomala' → French (reverse direction)
        conversations.append(bedrock_conversation(
            f"Que signifie cette phrase Ghomala' en français : {bbj}",
            f"Cette phrase Ghomala' signifie en français : {fr}"
        ))
        
        # Style 4: English request (for multilingual support)
        conversations.append(bedrock_conversation(
            f"How do you say in Ghomala': {fr}",
            f"In Ghomala', you say: {bbj}. The French equivalent is: {fr}"
        ))
    
    print(f"   ✅ Generated {len(conversations)} conversation pairs from {len(data)} translations")
    return conversations


# ============================================================================
# TRANSFORM 2: MasakhaNER sentences → vocabulary & culture conversations
# ============================================================================
def transform_ner(raw_path: Path) -> list:
    """
    Convert NER-annotated sentences into vocabulary-learning conversations.
    
    We extract the ENTITIES (names, places, dates) and create conversations 
    that teach Ghomala' vocabulary related to those entities.
    """
    print("🔄 Transforming MasakhaNER2 sentences...")
    
    with open(raw_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    conversations = []
    
    for item in data:
        sentence = item["sentence"].strip()
        tokens = item.get("tokens", [])
        tags = item.get("ner_tags", [])
        
        if not sentence or len(sentence) < 10:
            continue
        
        # Create a sentence-analysis conversation
        conversations.append(bedrock_conversation(
            f"Explique-moi cette phrase en Ghomala' : {sentence}",
            f"Voici l'analyse de cette phrase Ghomala' : '{sentence}'. "
            f"Cette phrase contient {len(tokens)} mots. "
            f"En Ghomala', la structure de la phrase suit un ordre spécifique "
            f"propre aux langues Grassfields Bantu."
        ))
        
        # Extract entities for vocabulary learning
        entities = []
        current_entity = []
        current_type = None
        
        for token, tag in zip(tokens, tags):
            if tag.startswith("B-"):
                if current_entity:
                    entities.append((" ".join(current_entity), current_type))
                current_entity = [token]
                current_type = tag[2:]
            elif tag.startswith("I-") and current_entity:
                current_entity.append(token)
            else:
                if current_entity:
                    entities.append((" ".join(current_entity), current_type))
                    current_entity = []
                    current_type = None
        if current_entity:
            entities.append((" ".join(current_entity), current_type))
        
        # Create entity-specific conversations
        type_labels = {"PER": "personne", "LOC": "lieu", "ORG": "organisation", "DATE": "date"}
        for entity_text, entity_type in entities:
            label = type_labels.get(entity_type, entity_type)
            conversations.append(bedrock_conversation(
                f"Quel est le mot '{entity_text}' en Ghomala' ?",
                f"'{entity_text}' est un nom de {label} en Ghomala'. "
                f"En Ghomala', les noms de {label} sont importants dans la culture Bamiléké."
            ))
    
    print(f"   ✅ Generated {len(conversations)} conversations from {len(data)} NER sentences")
    return conversations


# ============================================================================
# TRANSFORM 3: Dictionary entries → rich vocabulary conversations
# ============================================================================
def transform_dictionary(dict_path: Path) -> list:
    """
    Convert your personal Ghomala' dictionary into training conversations.
    
    Expected dictionary format (ghomala_dictionary.json):
    [
      {
        "ghomala": "mbʉ̂ə",
        "french": "chien",
        "category": "animal",
        "example": "Mbʉ̂ə gɔ̀ nə̀ ŋkwǎ' = Le chien est dans la maison",
        "cultural_note": "Les chiens sont des gardiens importants dans les concessions Bamiléké"
      }
    ]
    
    If you don't have the dictionary ready yet, this creates placeholder entries.
    """
    print("🔄 Transforming dictionary entries...")
    
    if not dict_path.exists():
        print("   ⚠️  Dictionary file not found. Creating template...")
        create_dictionary_template(dict_path)
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


def create_dictionary_template(dict_path: Path):
    """
    Creates a template JSON file for you to fill with your dictionary.
    
    ⚠️ BEN: Fill this file with entries from your physical Ghomala' dictionary!
    Even 50-100 entries will significantly improve the model.
    Focus on: greetings, family, food, numbers, daily life, ceremonies.
    """
    template = [
        {
            "ghomala": "REMPLACE_PAR_MOT_GHOMALA",
            "french": "REMPLACE_PAR_TRADUCTION",
            "category": "salutation|famille|nourriture|nombre|animal|corps|nature|ceremonie|quotidien",
            "example": "Phrase d'exemple en Ghomala' = Traduction française",
            "cultural_note": "Contexte culturel optionnel"
        },
        {
            "ghomala": "àkə̀",
            "french": "bonjour (matin)",
            "category": "salutation",
            "example": "Àkə̀, ò pɔ́ bɛ́ ? = Bonjour, comment vas-tu ?",
            "cultural_note": "Salutation utilisée le matin chez les Bamiléké"
        },
        {
            "ghomala": "mə̀ gɔ̀ wə̀",
            "french": "merci",
            "category": "salutation",
            "example": "",
            "cultural_note": "Expression de gratitude très utilisée"
        }
    ]
    
    dict_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dict_path, "w", encoding="utf-8") as f:
        json.dump(template, f, ensure_ascii=False, indent=2)
    
    print(f"   📝 Template created at {dict_path}")
    print(f"   ⚠️  IMPORTANT: Fill this file with your dictionary entries before re-running!")


# ============================================================================
# TRANSFORM 4: Hand-crafted cultural conversations (MOST IMPORTANT)
# ============================================================================
def generate_cultural_conversations() -> list:
    """
    Hand-crafted conversations that teach cultural context.
    
    These are the HIGHEST QUALITY training examples because they show the 
    model exactly how we want it to respond: with warmth, cultural depth, 
    and pedagogical patience.
    
    ⚠️ BEN: Add more of these! Ask your parents for proverbs, expressions, 
    and cultural explanations. Each one you add = better model quality.
    """
    print("🔄 Adding hand-crafted cultural conversations...")
    
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
    print(f"   ⚠️  TIP: Add more conversations here for better quality!")
    return conversations


# ============================================================================
# MAIN: Combine all sources → split → write JSONL
# ============================================================================
def main():
    print("🌍 NAM SA' — Dataset Transformation Pipeline")
    print("=" * 60)
    
    all_conversations = []
    
    # Transform each data source
    mafand_path = RAW_DIR / "mafand_mt_fr_bbj.json"
    ner_path = RAW_DIR / "masakhaner2_bbj.json"
    dict_path = DICT_DIR / "ghomala_dictionary.json"
    
    if mafand_path.exists():
        all_conversations.extend(transform_mafand(mafand_path))
    else:
        print(f"   ⚠️  {mafand_path} not found. Run 01_download_datasets.py first!")
    
    if ner_path.exists():
        all_conversations.extend(transform_ner(ner_path))
    else:
        print(f"   ⚠️  {ner_path} not found.")
    
    all_conversations.extend(transform_dictionary(dict_path))
    all_conversations.extend(generate_cultural_conversations())
    
    # Shuffle for training diversity
    random.shuffle(all_conversations)
    
    # Split: 90% train, 10% validation
    split_idx = int(len(all_conversations) * 0.9)
    train_data = all_conversations[:split_idx]
    val_data = all_conversations[split_idx:]
    
    # Write JSONL files (each line = one JSON object)
    train_path = PROCESSED_DIR / "train.jsonl"
    val_path = PROCESSED_DIR / "val.jsonl"
    
    with open(train_path, "w", encoding="utf-8") as f:
        for conv in train_data:
            # json.dumps with ensure_ascii=False preserves Ghomala' characters (ɔ, ɛ, ŋ, etc.)
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    
    with open(val_path, "w", encoding="utf-8") as f:
        for conv in val_data:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TRANSFORMATION SUMMARY")
    print("=" * 60)
    print(f"   Total conversations:  {len(all_conversations)}")
    print(f"   Training set (90%):   {len(train_data)}")
    print(f"   Validation set (10%): {len(val_data)}")
    print(f"\n   📁 train.jsonl: {train_path}")
    print(f"   📁 val.jsonl:   {val_path}")
    print(f"\n   📏 train.jsonl size: {train_path.stat().st_size / 1024:.1f} KB")
    print(f"   📏 val.jsonl size:   {val_path.stat().st_size / 1024:.1f} KB")
    
    # Show a sample
    print(f"\n   📝 Sample training entry (first line of train.jsonl):")
    with open(train_path, "r", encoding="utf-8") as f:
        sample = json.loads(f.readline())
        user_msg = sample["messages"][0]["content"][0]["text"]
        asst_msg = sample["messages"][1]["content"][0]["text"]
        print(f"      USER: {user_msg[:70]}...")
        print(f"      ASST: {asst_msg[:70]}...")
    
    print(f"\n   ➡️  Next step: python 03_upload_to_s3.py")
    print("=" * 60)


if __name__ == "__main__":
    main()
