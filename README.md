# NAM SA' — The Sun was raised

> AI-powered conversational agent for preserving the Ghomala' language using Amazon Nova 2 Sonic & Nova 2 Lite

An elder-like AI tutor that teaches and preserves **Ghomala' (Ghɔ́málá')**, a Bamiléké language spoken by ~1 million people in western Cameroon. The app supports voice-to-voice conversations, text translation, proverbs, and cultural teaching — powered by Amazon Bedrock fine-tuned models.

---

## 🏗️ Repo Structure

```
nkap-so-nova/
├── data/                              # 📊 Dataset & fine-tuning pipeline
│   ├── scripts/
│   │   ├── 01_download_datasets.py        # Download Masakhane datasets (MAFAND-MT, NER2, POS)
│   │   ├── 02_transform_to_jsonl.py       # Convert to Bedrock conversation JSONL format
│   │   ├── 03_upload_to_s3.py             # Upload train/val.jsonl to S3
│   │   └── 04_launch_fine_tuning.py       # Launch SFT/RFT job on Bedrock
│   ├── raw/                               # Raw downloaded datasets (gitignored)
│   ├── processed/                         # Final JSONL files (gitignored)
│   └── dictionary/
│       └── ghomala_dictionary.json        # Curated Ghomala' dictionary entries
│
├── backend/                           # 🖥️ FastAPI server (Docker → Fargate)
│   ├── src/
│   │   └── main.py                        # FastAPI + WebSocket + Bedrock integration
│   ├── tests/                             # (placeholder)
│   ├── config/                            # (placeholder)
│   ├── Dockerfile                         # Python 3.11 slim, uvicorn on port 8000
│   └── requirements.txt                   # fastapi, boto3, websockets, mangum, etc.
│
├── mobile/                            # 📱 React Native / Expo app
│   ├── App.js                             # Navigation stack (Home → Conversation)
│   ├── src/
│   │   ├── screens/
│   │   │   ├── HomeScreen.js              # Landing: 4 mode cards + voice CTA + quick phrases
│   │   │   └── ConversationScreen.js      # Chat UI: voice waveform, text input, message bubbles
│   │   ├── services/
│   │   │   └── api.js                     # REST (/api/chat, /api/translate) + WebSocket (/ws/voice)
│   │   └── theme/
│   │       └── index.js                   # Ghomala' cultural design system (maroon, gold, green)
│   ├── app.json                           # Expo config (mic + speech recognition permissions)
│   └── package.json                       # Expo 50, React Native 0.73
│
├── docs/                              # 📚 Documentation
│   └── fine-tuning/
│       ├── iam_setup.md                   # IAM role setup for Bedrock fine-tuning
│       └── SFT_vs_RFT_explained.md        # SFT vs RFT strategy explained
│
├── requirements.txt                   # Data pipeline deps (datasets, boto3, pandas)
└── README.md
```

---

## 🚀 Quick Start

### 1. Fine-Tuning Pipeline (data → model)

```bash
# Install data pipeline dependencies
pip install -r requirements.txt

# Download Masakhane/Ghomala datasets from HuggingFace
cd data/scripts
python 01_download_datasets.py

# Transform to Bedrock conversation JSONL format (train.jsonl + val.jsonl)
python 02_transform_to_jsonl.py              # → cappé à 20,000 (AWS Nova Lite)
python 02_transform_to_jsonl.py --no-limit    # → TOUS les 48,897 samples (open source)

# Upload to S3 bucket
python 03_upload_to_s3.py

# Launch SFT fine-tuning on Bedrock
python 04_launch_fine_tuning.py --mode sft
```

### 2. Backend (FastAPI)

```bash
cd backend

# Install backend dependencies
pip install -r requirements.txt

# Run locally
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Or run with Docker
docker build -t namsa-backend .
docker run -p 8000:8000 -e AWS_REGION=us-east-1 namsa-backend
```

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Text conversation (Nova Lite) |
| `POST` | `/api/translate` | Translation (FR ↔ Ghomala') |
| `WS` | `/ws/voice` | Bidirectional voice streaming (Nova Sonic) |

### 3. Mobile App (Expo)

```bash
cd mobile
npm install
npx expo start
```

**Modes:** Tutor (📖) · Conversation (💬) · Proverbs (🌿) · Translate (🔄)

---

## 🧠 Training Strategy

| Phase | Method | Data | Goal |
|-------|--------|------|------|
| 1 | **SFT** | ~3,000-5,000 conversation pairs | Teach Ghomala' vocabulary & grammar |
| 2 | **RFT** | Prompts + Bedrock reward model | Polish quality, tone & cultural accuracy |

**Evaluation:** We use **Amazon Bedrock Model Evaluation** to compare SFT checkpoints, measuring Ghomala' character accuracy, translation quality, and cultural appropriateness before promoting a model version.

See [docs/fine-tuning/SFT_vs_RFT_explained.md](docs/fine-tuning/SFT_vs_RFT_explained.md) for details.

---

## ⚙️ Architecture

```
┌─────────────┐         ┌──────────────────┐        ┌──────────────────────────────────┐
│  Mobile App │──REST──►│                  │──────►│  Nova 2 Lite fine-tuned (text)    │
│  (Expo)     │         │  FastAPI         │        └──────────────────────────────────┘
│             │──WS────►│  on Fargate      │        ┌──────────────────────────────────┐
│  PCM 16kHz  │◄═══════►│  (port 8000)     │◄══════►│  Nova 2 Sonic (speech-to-speech) │
│  streaming  │ binary  │                  │ stream │  Bidirectional streaming — audio  │
│  audio      │ audio   │                  │        │  never stops flowing             │
└─────────────┘ frames  │                  │        └──────────────────────────────────┘
                        │                  │        ┌──────────────────────────────────┐
                        │                  │──────►│  Ghomala' Dictionary Tool         │
                        │                  │        │  (Bedrock tool_use)              │
                        └──────────────────┘        └──────────────────────────────────┘
                                │
                        ┌───────▼──────────┐
                        │  Guardrails for  │
                        │  Bedrock         │
                        └──────────────────┘
```

### Voice Pipeline (Nova 2 Sonic)

Nova Sonic is a **speech-to-speech** model — it receives raw audio and produces raw audio. There is no intermediate text transcription step. The WebSocket connection carries **binary PCM audio frames** (16 kHz, mono) in both directions simultaneously. Audio never stops flowing: the user speaks, Sonic listens, thinks, and responds — all on the same persistent stream. This is the core technical challenge and the differentiator for Voice AI.

### Key Services

- **Nova 2 Sonic** (`amazon.nova-sonic-v1:0`): bidirectional streaming speech-to-speech via WebSocket binary audio frames
- **Nova 2 Lite** (`amazon.nova-lite-v1:0`): text chat & translation (fine-tuned via SFT on Bedrock)
- **Bedrock tool_use**: Ghomala' dictionary lookups integrated as function calls during conversation
- **Guardrails for Bedrock**: content filters ensuring culturally respectful responses — blocks disrespectful or inaccurate content about Ghomala' culture, traditions, and people
- **Fargate (ECS)**: persistent container hosting for WebSocket connections (no cold starts, no timeout limits)

---

## 🛡️ Safety & Guardrails

We use **Amazon Bedrock Guardrails** to ensure the AI is a responsible cultural ambassador:

| Guardrail | Purpose |
|-----------|---------|
| **Cultural respect filter** | Prevents disrespectful, inaccurate, or stereotypical statements about Bamiléké culture |
| **Content moderation** | Blocks harmful, hateful, or inappropriate content in all languages |
| **Topic restrictions** | Keeps conversations focused on language learning, culture, and translation |
| **Sensitive info filter** | Prevents the model from generating or requesting personal data |

Guardrails are applied at the Bedrock inference layer — every call to Nova Lite and Nova Sonic passes through them before reaching the user.

---

## 📋 Hackathon
- **Competition:** Amazon Nova AI Hackathon
- **Category:** Voice AI
- **Deadline:** March 16, 2026, 5:00 PM PT
- **Prize:** $3,000 + $5,000 AWS Credits (Voice AI) / $15,000 (1st Overall)

## 📜 License
MIT
