"""
Test fine-tuned Nova 2 Lite model vs dictionary entries.
Compares the custom model's translations against known Ghomala' dictionary entries.
"""
import boto3
import json
import time

session = boto3.Session(profile_name='ceo', region_name='us-east-1')
client = session.client('bedrock-runtime')

DEPLOYMENT_ARN = "arn:aws:bedrock:us-east-1:685497515185:custom-model-deployment/0845rha0mvyz"
BASE_MODEL = "us.amazon.nova-2-lite-v1:0"

SYSTEM_PROMPT = (
    "Tu es NAM SA' (Le Soleil S'est Levé), un agent IA spécialisé dans "
    "la préservation et l'enseignement de la langue Ghomala' (Ghɔ̀málá'). "
    "Tu parles Ghomala', Français et Anglais."
)

# Test cases from the dictionary
TEST_CASES = [
    {"question": "Comment dit-on 'bonjour' en Ghomala' ?", "expected_keywords": ["saluer", "mbʉ̀ɔ"]},
    {"question": "Comment dit-on 'maison' en Ghomala' ?", "expected_keywords": ["ŋkwà", "ndʉ̂ɔ"]},
    {"question": "Comment dit-on 'eau' en Ghomala' ?", "expected_keywords": ["shyə̀"]},
    {"question": "Comment dit-on 'manger' en Ghomala' ?", "expected_keywords": ["dzʉ̌", "pfʉ̌"]},
    {"question": "Comment dit-on 'père' en Ghomala' ?", "expected_keywords": ["tá", "ta'"]},
    {"question": "Comment dit-on 'mère' en Ghomala' ?", "expected_keywords": ["má", "ma'"]},
    {"question": "Traduis en Ghomala' : je t'aime", "expected_keywords": ["Ghomala'"]},
    {"question": "Dis-moi un proverbe Bamiléké", "expected_keywords": ["proverbe", "Bamiléké", "sagesse"]},
    {"question": "Comment salue-t-on un chef en Ghomala' ?", "expected_keywords": ["Fɔ̀", "chef", "saluer"]},
    {"question": "How do you say 'water' in Ghomala'?", "expected_keywords": ["Ghomala'", "water"]},
]


def invoke_model(model_id, question, label=""):
    body = json.dumps({
        "system": [{"text": SYSTEM_PROMPT}],
        "messages": [{"role": "user", "content": [{"text": question}]}],
        "inferenceConfig": {"maxTokens": 300, "temperature": 0.3}
    })
    try:
        resp = client.invoke_model(
            modelId=model_id,
            body=body,
            contentType="application/json",
            accept="application/json"
        )
        result = json.loads(resp["body"].read())
        return result["output"]["message"]["content"][0]["text"]
    except Exception as e:
        return f"[ERROR: {e}]"


def main():
    print("=" * 80)
    print("NAM SA' — Fine-tuned Model Test: Custom vs Base")
    print("=" * 80)

    for i, test in enumerate(TEST_CASES, 1):
        q = test["question"]
        print(f"\n{'─' * 80}")
        print(f"Test {i}: {q}")
        print(f"{'─' * 80}")

        # Fine-tuned model
        print("\n🎯 FINE-TUNED MODEL:")
        ft_answer = invoke_model(DEPLOYMENT_ARN, q.replace("'", "'"))
        print(f"   {ft_answer[:500]}")

        time.sleep(0.5)

        # Base model
        print("\n📦 BASE MODEL:")
        base_answer = invoke_model(BASE_MODEL, q.replace("'", "'"))
        print(f"   {base_answer[:500]}")

        time.sleep(0.5)

    print(f"\n{'=' * 80}")
    print("TEST COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
