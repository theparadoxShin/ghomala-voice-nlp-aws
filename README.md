# NAM SA' — Le Soleil S'est Levé

**AI-powered conversational agent for preserving the Ghomala' language, built with Amazon Nova 2 Sonic and Nova 2 Lite fine-tuned on Amazon Bedrock.**

NAM SA' is a mobile application that teaches and preserves **Ghomala' (Ghɔ́málá')**, a tonal Bantu language spoken by approximately 1 million people in the West Region of Cameroon. Ghomala' is classified as a **vulnerable language** by UNESCO — it has no standardized writing system, very few digital resources, and its speakers are aging. NAM SA' uses voice AI and a fine-tuned language model to make learning Ghomala' accessible, interactive, and culturally grounded.

The name means *"The Sun Has Risen"* in Ghomala' — a metaphor for cultural awakening.

---

## The Problem

Ghomala' is disappearing. Young Cameroonians grow up speaking French or English and lose their mother tongue. There are:
- No Ghomala' courses on Duolingo, Google Translate, or any mainstream platform
- No large-scale digital corpus or NLP model for the language
- No voice assistant that understands or speaks Ghomala'
- Only a handful of physical dictionaries, written by missionaries decades ago

We built NAM SA' to change that.

---

## What NAM SA' Does

| Feature | Description |
|---------|-------------|
| **Real-time voice conversation** | Speak naturally and get spoken responses — powered by Nova 2 Sonic bidirectional streaming |
| **Text chat** | Typed conversation with the AI tutor for learning vocabulary, grammar, and cultural context |
| **Dictionary & Translation** | Google Translate-style interface between French, English, and Ghomala' |
| **Proverbs** | Browse 20+ categorized Bamiléké proverbs with meanings, Ghomala' translations, and audio playback |
| **Vocabulary tutor** | Structured learning path: 3 levels, 15 topics, 75+ words with on-demand Ghomala' translation and TTS |
| **Text-to-Speech** | Every translation and response can be read aloud via Amazon Polly |
| **Bilingual interface** | Full French/English UI with language switching |

---

## Architecture

```
                                    ┌──────────────────────────────────────┐
                                    │  Amazon Bedrock                      │
                                    │                                      │
                              ┌─────┤  Nova 2 Lite (fine-tuned SFT)       │
                              │     │  Custom deployment — on-demand       │
            ┌─────────────┐   │     │  Text chat, translation, dictionary  │
            │             │   │     │                                      │
            │  Mobile App ├───┤     │  Nova 2 Sonic                        │
            │  (Expo /    │   │     │  Bidirectional speech-to-speech      │
            │  React      │   │     │  Real-time streaming via WebSocket   │
            │  Native)    │   │     │                                      │
            │             │   │     └──────────────────────────────────────┘
            └──────┬──────┘   │
                   │          │     ┌──────────────────────────────────────┐
                   │   REST   │     │  Amazon Polly (Neural TTS)           │
                   │   & WS   ├─────┤  French: Lea / English: Matthew     │
                   │          │     │  MP3 audio for text-to-speech        │
                   ▼          │     └──────────────────────────────────────┘
            ┌─────────────┐   │
            │  FastAPI     │   │     ┌──────────────────────────────────────┐
            │  Backend     ├───┤     │  Amazon Transcribe                   │
            │  on AWS      │   │     │  Speech-to-text for voice pipeline   │
            │  Fargate     │   └─────┤  French language detection           │
            │  (ECS)       │         └──────────────────────────────────────┘
            │              │
            │  ALB (HTTP)  │         ┌──────────────────────────────────────┐
            │  ECR (Docker)│─────────┤  Amazon S3                           │
            └─────────────┘          │  Training data & temp audio storage  │
                                     └──────────────────────────────────────┘
```

### Two Voice Pipelines

NAM SA' implements two distinct voice architectures, each serving a different interaction pattern:

**1. Nova 2 Sonic — Real-time speech-to-speech** (`/ws/sonic`)

Nova Sonic is a speech foundation model that handles audio input and output natively. There is no intermediate transcription or synthesis step — the model receives raw PCM audio (16 kHz) and produces spoken audio (24 kHz) directly. The WebSocket connection uses the Smithy-based `aws-sdk-bedrock-runtime` SDK for bidirectional streaming via `InvokeModelWithBidirectionalStream`. This is the primary voice experience.

**2. Voice pipeline — Record-then-send** (`/ws/live`)

For scenarios where the user records a complete utterance (with silence detection), we use a three-stage pipeline:
- **Amazon Transcribe** converts the audio clip to text
- **Nova 2 Lite (fine-tuned)** generates a Ghomala'-aware response
- **Amazon Polly** synthesizes the response back to speech (MP3)

This pipeline gives higher-quality text responses (leveraging the fine-tuned model) while the Sonic pipeline provides the most natural conversational flow.

---

## Backend API

The backend is a FastAPI application deployed on AWS Fargate behind an Application Load Balancer.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — returns model IDs and status |
| `POST` | `/api/chat` | Text conversation with modes: tutor, conversation, proverb, translate |
| `POST` | `/api/translate` | Translation between French, English, and Ghomala' |
| `POST` | `/api/tts` | Text-to-Speech via Amazon Polly — returns base64 MP3 |
| `WS` | `/ws/sonic` | Nova 2 Sonic bidirectional speech-to-speech streaming |
| `WS` | `/ws/live` | Record-then-send voice (Transcribe → Nova Lite → Polly) |
| `WS` | `/ws/voice` | Legacy voice pipeline (PCM variant) |

---

## Mobile App

Built with **React Native** and **Expo SDK 55**. Six screens, a shared TTS service, and a bilingual context provider.

### Screens

| Screen | Route | Purpose |
|--------|-------|---------|
| **HomeScreen** | `Home` | Landing page — logo, language selector (FR/EN), 4 mode cards, voice CTA |
| **LiveScreen** | `Dialogue` | Real-time voice conversation — tap mic, speak, auto-silence detection, continuous flow |
| **DialogueScreen** | `Chat` | Text chat with the AI tutor — message bubbles, TTS on every message |
| **DictionaryScreen** | `Dictionary` | Google Translate-style interface — source/target language picker, swap, TTS |
| **ProverbsScreen** | `Proverbs` | Browse proverbs by category — expand for meaning, translate to Ghomala', listen |
| **TutorScreen** | `Tutor` | Structured vocabulary learning — 3 levels, 15 topics, word cards with TTS |

### Key Technical Choices

- **expo-audio** for audio recording (with metering for silence detection) and playback
- **expo-file-system** for writing base64 audio to temp files before playback
- **expo-localization** + **AsyncStorage** for persisted language preference
- **Custom TTS service** (`tts.js`) — calls backend `/api/tts`, caches audio files, manages playback lifecycle
- **No third-party state management** — React Context for language, `useState`/`useRef` for local screen state

### Design System

Colors are drawn from the NAM SA' logo — a sun rising over banana leaves:
- **Maroon (#7A2E1E)** — primary, headings, from the "NAM SA'" text in the logo
- **Sun Gold (#E8A020)** — secondary, CTAs, active states, from the sun illustration
- **Forest Green (#2D7A3A)** — accent, success, from the banana leaves
- **Cream (#FFF8F0)** — background surfaces

---

## Fine-Tuning

### Data Pipeline

We built a 6-step pipeline to prepare training data for Amazon Bedrock Supervised Fine-Tuning (SFT):

| Script | Purpose |
|--------|---------|
| `00_extract_dictionary_from_pdf.py` | Extract 4,929 dictionary entries from a scanned Ghomala' PDF dictionary using Gemini Vision API |
| `01_download_datasets.py` | Download Masakhane open-source datasets (MAFAND-MT, AfriQA, XLSUM) from HuggingFace |
| `02_transform_to_jsonl.py` | Convert all sources to Bedrock conversation JSONL format (capped at 20,000 samples) |
| `03_upload_to_s3.py` | Upload training data to S3 |
| `04_launch_fine_tuning.py` | Launch SFT job on Amazon Bedrock |
| `05_optimize_dataset.py` | Select a balanced subset of 2,000 samples for faster training |

### Training Details

- **Base model:** Amazon Nova 2 Lite (`amazon.nova-2-lite-v1:0:256k`)
- **Method:** Supervised Fine-Tuning (SFT)
- **Dataset:** 2,000 balanced samples — 61 cultural entries, 646 dictionary entries, 646 French translation pairs, 647 English translation pairs
- **Hyperparameters:** 1 epoch, batch size 1 (maximum for Nova on Bedrock), learning rate 1e-4
- **Training time:** ~5 hours 24 minutes
- **Deployment:** On-demand custom model deployment (not Provisioned Throughput)

### Data Sources

| Source | Entries | Content |
|--------|---------|---------|
| Ghomala' PDF Dictionary | 4,929 | Word definitions with phonetic transcriptions, extracted page-by-page via vision model |
| Masakhane MAFAND-MT | ~6,000 | French-Ghomala' parallel translations from the open-source NLP project |
| Masakhane AfriQA | ~800 | Question-answer pairs in African languages |
| Cultural entries | 61 | Hand-curated greetings, proverbs, and cultural context |

### Fine-Tuned vs Base Model

The fine-tuned model produces dramatically better results for Ghomala':

| Prompt | Base Nova 2 Lite | Fine-Tuned Nova 2 Lite |
|--------|------------------|------------------------|
| "Traduis 'bonjour' en Ghomala'" | Invents fake words, confuses with Beti-Pahuin language | Returns correct Ghomala' form with tonal marks |
| "Donne un proverbe Bamiléké" | Generic African proverb with no cultural context | Authentic Bamiléké proverb with meaning and cultural explanation |
| "Comment dit-on 'eau' en Ghomala'?" | Long hallucinated paragraph | Concise: the correct word with category |

---

## AWS Services Used

| Service | Role |
|---------|------|
| **Amazon Bedrock** | Fine-tuning (SFT) + inference (Converse API) for Nova 2 Lite |
| **Amazon Nova 2 Sonic** | Real-time bidirectional speech-to-speech via Bedrock streaming |
| **Amazon Nova 2 Lite** | Text generation — chat, translation, proverbs, vocabulary |
| **Amazon Polly** | Neural text-to-speech (Lea for French, Matthew for English) |
| **Amazon Transcribe** | Speech-to-text for the record-then-send voice pipeline |
| **Amazon ECS (Fargate)** | Serverless container hosting — no cold starts, persistent WebSocket support |
| **Amazon ECR** | Docker image registry for the backend |
| **Elastic Load Balancing (ALB)** | HTTP/WebSocket routing to Fargate tasks |
| **Amazon S3** | Training data storage and temporary audio file staging |
| **AWS IAM** | Task roles for Bedrock, Polly, Transcribe, S3 access |

---

## Challenges & Lessons Learned

### Ghomala' is a true low-resource language

There is almost no Ghomala' data on the internet. The largest source we found was a scanned PDF dictionary from the 1970s. We had to extract 4,929 entries using a vision model (Gemini) page by page, then manually curate and transform them into training pairs. Most NLP tools (tokenizers, language detectors, TTS engines) have never seen Ghomala'.

### Fine-tuning Nova on Bedrock is constrained

- **Batch size is capped at 1** for Nova 2 Lite on Bedrock — no parallelism during training
- Our first attempt with 18,000 samples and 3 epochs projected ~48 days of training time
- We solved this by carefully curating a balanced subset of **2,000 samples** trained for 1 epoch, completed in ~5.5 hours
- Provisioned Throughput was not available for our account — we discovered and used the newer `CreateCustomModelDeployment` API for on-demand inference

### Sonic SDK is new and different

Nova 2 Sonic uses a **Smithy-based Python SDK** (`aws-sdk-bedrock-runtime`) that is separate from boto3. It requires explicit credential synchronization from the boto3 session to environment variables, since the Smithy SDK only supports `EnvironmentCredentialsResolver`. The bidirectional streaming protocol has a specific event sequence (sessionStart → promptStart → contentStart → audioInput → contentEnd) that must be followed exactly.

### TTS for Ghomala'

No TTS engine supports Ghomala' natively. We use Amazon Polly's French neural voice (Lea) as a fallback — French phonetics are the closest match to Ghomala' pronunciation. The results are imperfect but functional for a learning context.

---

## Project Structure

```
nkap-so-nova/
├── backend/
│   ├── src/
│   │   └── main.py                    # FastAPI app — REST + 3 WebSocket endpoints + Bedrock/Polly/Transcribe
│   ├── Dockerfile                     # Python 3.12-slim, uvicorn
│   └── requirements.txt               # fastapi, boto3, aws-sdk-bedrock-runtime, etc.
│
├── mobile/
│   ├── App.js                         # Navigation: Home → Dictionary → Dialogue → Chat → Proverbs → Tutor
│   ├── src/
│   │   ├── screens/
│   │   │   ├── HomeScreen.js          # Landing — logo, language selector, 4 mode cards, voice CTA
│   │   │   ├── LiveScreen.js          # Real-time voice — mic with silence detection, WebSocket streaming
│   │   │   ├── DialogueScreen.js      # Text chat — message bubbles, TTS playback per message
│   │   │   ├── DictionaryScreen.js    # Translation — language picker, swap, source/target text boxes
│   │   │   ├── ProverbsScreen.js      # Proverbs — categories, expand for meaning, translate to Ghomala'
│   │   │   ├── TutorScreen.js         # Vocabulary — 3 levels, 15 topics, word cards with TTS
│   │   │   └── ConversationScreen.js  # Alternate voice chat UI (with waveform animations)
│   │   ├── services/
│   │   │   ├── api.js                 # REST client (chat, translate, TTS) + WebSocket helper
│   │   │   └── tts.js                 # Shared TTS service — fetchTTS → base64 → file → expo-audio playback
│   │   ├── context/
│   │   │   └── LanguageContext.js     # i18n provider — FR/EN translations, persisted via AsyncStorage
│   │   ├── data/
│   │   │   ├── proverbs.js            # 20+ Bamiléké proverbs organized by 6 categories
│   │   │   └── vocabulary.js          # 75+ words across 3 levels and 15 topics
│   │   └── theme/
│   │       └── index.js               # Design tokens — colors, typography, spacing, shadows
│   ├── app.json                       # Expo config — permissions, plugins, API URL
│   └── package.json                   # Expo 55, React Native 0.83, React 19
│
├── data/
│   ├── scripts/
│   │   ├── 00_extract_dictionary_from_pdf.py   # PDF → 4,929 dictionary entries (Gemini Vision)
│   │   ├── 01_download_datasets.py             # Download Masakhane datasets from HuggingFace
│   │   ├── 02_transform_to_jsonl.py            # Convert to Bedrock conversation JSONL
│   │   ├── 03_upload_to_s3.py                  # Upload to S3
│   │   ├── 04_launch_fine_tuning.py            # Launch SFT on Bedrock
│   │   └── 05_optimize_dataset.py              # Select balanced 2,000-sample subset
│   └── dictionary/
│       └── ghomala_dictionary.json             # 4,929 extracted dictionary entries
│
├── docs/
│   └── fine-tuning/
│       ├── iam_setup.md
│       └── SFT_vs_RFT_explained.md
│
└── README.md
```

---

## Getting Started

### Backend

```bash
cd backend
pip install -r requirements.txt

# Run locally
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# Or with Docker
docker build -t nam-sa-backend .
docker run -p 8000:8000 \
  -e AWS_REGION=us-east-1 \
  -e NOVA_LITE_MODEL_ID=<your-model-deployment-arn> \
  nam-sa-backend
```

### Mobile

```bash
cd mobile
npm install
npx expo start
```

Scan the QR code with Expo Go on your phone. The app connects to the backend via the URL configured in `app.json` → `expo.extra.API_URL`.

### Fine-Tuning Pipeline

```bash
pip install -r requirements.txt
cd data/scripts

python 00_extract_dictionary_from_pdf.py --pdf path/to/dictionary.pdf
python 01_download_datasets.py
python 02_transform_to_jsonl.py
python 05_optimize_dataset.py    # Select balanced 2,000-sample subset
python 03_upload_to_s3.py
python 04_launch_fine_tuning.py --mode sft
```

---

## Team

Built for the **Amazon Nova AI Hackathon** (Voice AI category) — March 2026.

## License

MIT
