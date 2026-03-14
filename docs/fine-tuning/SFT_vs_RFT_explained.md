# SFT vs RFT — Explained Simply

## Supervised Fine-Tuning (SFT) — "Learning from a textbook"

```
You show the model:  "Question: Comment dit-on bonjour en Ghomala'?"
                     "Answer: En Ghomala', bonjour se dit àkə̀"

The model learns:    "When asked about Ghomala' greetings → respond like this"
```

**How it works:**
1. You give labeled pairs: (input → expected output)
2. The model adjusts its weights to match your examples
3. After training, it generates similar responses for new inputs

**When to use:** Teaching NEW KNOWLEDGE (Ghomala' vocabulary, grammar, cultural context)

**Our data:** ~3,000-5,000 conversation pairs from MAFAND-MT + dictionary + manual entries

---

## Reinforcement Fine-Tuning (RFT) — "Learning from a teacher's feedback"

```
Model generates:   "Bonjour en Ghomala' se dit XYZ" 
Grader scores:     Score = 0.8/1.0 (good but missing cultural context)
Model adjusts:     Next time → add cultural context for higher score
```

**How it works:**
1. You give PROMPTS only (no expected answers)
2. The model generates responses on its own
3. A GRADER (Lambda function) scores each response (0 to 1)
4. The model learns to maximize its score

**When to use:** POLISHING quality after SFT (better tone, accuracy, completeness)

**Our grader checks:**
- Contains Ghomala' characters? (+0.3)
- Translation seems correct? (+0.3) 
- Includes cultural context? (+0.2)
- Warm, encouraging tone? (+0.2)

---

## Our Strategy: SFT First, Then RFT

```
Step 1: SFT → Teach the model Ghomala' (Day 3)
        Input: 3,000+ conversation pairs
        Result: Model knows Ghomala' vocabulary

Step 2: RFT → Polish the quality (Day 4, if time)
        Input: Prompts + Lambda grader
        Result: Model responses are more accurate and natural
```

## Certification Relevance

| Concept | AWS ML Associate | AWS Developer Associate |
|---------|-----------------|----------------------|
| SFT on Bedrock | ✅ Model customization | ✅ API usage |
| RFT on Bedrock | ✅ Advanced ML technique | ✅ Lambda integration |
| S3 data pipeline | ✅ Data engineering | ✅ S3 operations |
| IAM roles | ✅ Security | ✅ Security |
| Model evaluation | ✅ ML metrics | — |
