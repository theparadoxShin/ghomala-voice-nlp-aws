"""
NAM SA' — Backend Server (AWS)
FastAPI + WebSocket for Ghomala' language AI.

Architecture:
  Mobile App ─── REST ──▶ FastAPI ──▶ Nova 2 Lite fine-tuned (Bedrock converse)
  Mobile App ─── WS ────▶ FastAPI ──▶ Transcribe → Nova 2 Lite → Polly (voice pipeline)
  Mobile App ─── WS ────▶ FastAPI ──▶ Nova 2 Sonic (real-time speech-to-speech)

Models:
  - Nova 2 Lite (fine-tuned): Text chat, translation, dictionary — via Bedrock converse()
  - Nova 2 Sonic: Real-time bidirectional speech-to-speech — via InvokeModelWithBidirectionalStream
  - Amazon Transcribe Streaming: Speech-to-text for voice input (fallback pipeline)
  - Amazon Polly: Text-to-speech for voice output (fallback pipeline)

Run locally:  uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
Deploy:       Docker → AWS Fargate (ECS)
"""

import asyncio
import base64
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import boto3

# Smithy-based SDK for Nova 2 Sonic bidirectional streaming
from aws_sdk_bedrock_runtime.client import (
    BedrockRuntimeClient as SonicBedrockClient,
    InvokeModelWithBidirectionalStreamOperationInput,
)
from aws_sdk_bedrock_runtime.models import (
    InvokeModelWithBidirectionalStreamInputChunk,
    BidirectionalInputPayloadPart,
)
from aws_sdk_bedrock_runtime.config import Config as SonicConfig
from smithy_aws_core.identity.environment import EnvironmentCredentialsResolver

logger = logging.getLogger("namsa")
logging.basicConfig(level=logging.INFO)

# ============================================================================
# CONFIGURATION
# ============================================================================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Fine-tuned model deployed via on-demand custom model deployment
# Falls back to base Nova 2 Lite if deployment ARN is not set
NOVA_LITE_MODEL_ID = os.getenv(
    "NOVA_LITE_MODEL_ID",
    "arn:aws:bedrock:us-east-1:685497515185:custom-model-deployment/0845rha0mvyz"
)

# Polly voice for French TTS
POLLY_VOICE_ID = os.getenv("POLLY_VOICE_ID", "Lea")  # French female voice
POLLY_ENGINE = "neural"

# Nova 2 Sonic — real-time speech-to-speech
NOVA_SONIC_MODEL_ID = os.getenv("NOVA_SONIC_MODEL_ID", "amazon.nova-2-sonic-v1:0")
NOVA_SONIC_VOICE_ID = os.getenv("NOVA_SONIC_VOICE_ID", "matthew")

SYSTEM_PROMPT = (
    "Tu es NAM SA' (Le Soleil S'est Levé), un agent IA conversationnel "
    "dédié à la préservation et l'enseignement de la langue Ghomala' (Ghɔ́málá'), "
    "une langue Bamiléké parlée par environ 1 million de personnes dans la région "
    "Ouest du Cameroun.\n\n"
    "Tu te comportes comme un(e) ancien(ne) bienveillant(e) du village Bamiléké. "
    "Tu es patient(e), encourageant(e), et tu célèbres chaque effort d'apprentissage.\n\n"
    "Tes capacités:\n"
    "- Traduire entre Ghomala', Français et Anglais\n"
    "- Enseigner le vocabulaire Ghomala' avec contexte culturel\n"
    "- Partager des proverbes Bamiléké et leur sagesse\n"
    "- Corriger la prononciation avec bienveillance\n"
    "- Expliquer la grammaire tonale du Ghomala'\n\n"
    "Règles:\n"
    "- Toujours donner le contexte culturel quand c'est pertinent\n"
    "- Utiliser les caractères spéciaux corrects (ɔ, ɛ, ŋ, ə) et les tons (à, á, â, ǎ)\n"
    "- Encourager l'apprenant même en cas d'erreur\n"
    "- Répondre dans la langue demandée par l'utilisateur"
)

# ============================================================================
# AWS CLIENTS
# ============================================================================
bedrock_runtime = None
polly_client = None
transcribe_client = None


def _sync_credentials_to_env():
    """
    Extract credentials from boto3's default chain (supports ECS task roles,
    instance profiles, env vars, ~/.aws) and set as env vars so the Smithy SDK's
    EnvironmentCredentialsResolver can pick them up.
    """
    session = boto3.Session(region_name=AWS_REGION)
    creds = session.get_credentials()
    if creds:
        resolved = creds.get_frozen_credentials()
        os.environ["AWS_ACCESS_KEY_ID"] = resolved.access_key
        os.environ["AWS_SECRET_ACCESS_KEY"] = resolved.secret_key
        if resolved.token:
            os.environ["AWS_SESSION_TOKEN"] = resolved.token


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bedrock_runtime, polly_client, transcribe_client
    logger.info("Initializing AWS clients...")
    bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)
    polly_client = boto3.client("polly", region_name=AWS_REGION)
    transcribe_client = boto3.client("transcribe", region_name=AWS_REGION)
    # Sync credentials for Smithy SDK (Nova Sonic)
    _sync_credentials_to_env()
    logger.info(f"AWS clients ready (region={AWS_REGION}, model={NOVA_LITE_MODEL_ID})")
    logger.info(f"Nova 2 Sonic available: model={NOVA_SONIC_MODEL_ID}, voice={NOVA_SONIC_VOICE_ID}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="NAM SA' API",
    description="Ghomala' Language Preservation AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# DATA MODELS
# ============================================================================
class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "fr"
    target_lang: str = "bbj"


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str = "tutor"


class ChatResponse(BaseModel):
    response: str
    session_id: str
    mode: str
    timestamp: str


class TTSRequest(BaseModel):
    text: str
    language: str = "fr"


# ============================================================================
# CORE: Call fine-tuned Nova 2 Lite via Bedrock converse()
# ============================================================================
async def call_nova_lite(user_text: str, system_override: str | None = None) -> str:
    """Single place for all Nova 2 Lite calls."""
    system_text = system_override or SYSTEM_PROMPT
    try:
        response = bedrock_runtime.converse(
            modelId=NOVA_LITE_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": user_text}]}],
            system=[{"text": system_text}],
            inferenceConfig={"maxTokens": 800, "temperature": 0.7},
        )
        return response["output"]["message"]["content"][0]["text"]
    except Exception as e:
        logger.error(f"Nova Lite error: {e}")
        raise


# ============================================================================
# REST ENDPOINTS
# ============================================================================
@app.get("/")
async def root():
    return {
        "app": "NAM SA'",
        "meaning": "Le soleil s'est levé",
        "description": "Ghomala' Language Preservation AI",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat",
            "translate": "/api/translate",
            "tts": "/api/tts",
            "voice": "/ws/voice",
            "live": "/ws/live",
            "sonic": "/ws/sonic",
            "health": "/health",
        },
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "region": AWS_REGION,
        "model": NOVA_LITE_MODEL_ID,
        "sonic_model": NOVA_SONIC_MODEL_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Text chat — uses Nova 2 Lite (fine-tuned)."""
    session_id = request.session_id or str(uuid.uuid4())

    mode_instructions = {
        "tutor": "L'utilisateur veut apprendre un mot ou une expression. Enseigne avec patience.",
        "conversation": "Dialogue libre. Maintiens le contexte et corrige gentiment les erreurs.",
        "proverb": "Partage un proverbe Bamiléké pertinent avec son explication.",
        "translate": "Traduis la phrase demandée entre Ghomala', Français et Anglais.",
    }
    instruction = mode_instructions.get(request.mode, mode_instructions["tutor"])
    full_prompt = f"[Mode: {request.mode}] {instruction}\n\nUtilisateur: {request.message}"

    try:
        answer = await call_nova_lite(full_prompt)
        return ChatResponse(
            response=answer,
            session_id=session_id,
            mode=request.mode,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/translate")
async def translate(request: TranslateRequest):
    """Quick translation endpoint."""
    lang_map = {"fr": "Français", "en": "Anglais", "bbj": "Ghomala'"}
    src = lang_map.get(request.source_lang, request.source_lang)
    tgt = lang_map.get(request.target_lang, request.target_lang)

    prompt = f"Traduis de {src} vers {tgt}: {request.text}"
    try:
        result = await call_nova_lite(prompt)
        return {
            "original": request.text,
            "translation": result,
            "source_lang": request.source_lang,
            "target_lang": request.target_lang,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tts")
async def text_to_speech(request: TTSRequest):
    """
    Text-to-Speech via Amazon Polly.
    Returns base64-encoded MP3 audio.
    Language: 'fr' → Lea, 'en' → Matthew, 'bbj' → Lea (French voice for Ghomala').
    """
    voice_map = {
        "fr": ("Lea", "fr-FR"),
        "en": ("Matthew", "en-US"),
        "bbj": ("Lea", "fr-FR"),  # Use French voice for Ghomala' (closest phonetics)
    }
    voice_id, lang_code = voice_map.get(request.language, ("Lea", "fr-FR"))

    try:
        response = polly_client.synthesize_speech(
            Text=request.text,
            OutputFormat="mp3",
            VoiceId=voice_id,
            Engine="neural",
            LanguageCode=lang_code,
        )
        audio_bytes = response["AudioStream"].read()
        audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
        return {
            "audio": audio_b64,
            "mime_type": "audio/mpeg",
            "voice": voice_id,
            "language": request.language,
        }
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=f"TTS failed: {e}")


# ============================================================================
# VOICE PIPELINE: Transcribe → Nova 2 Lite → Polly
# ============================================================================
async def transcribe_audio(audio_bytes: bytes) -> str:
    """Transcribe audio bytes to text using Amazon Transcribe (batch mode)."""
    import tempfile, os as _os
    job_name = f"namsa-{uuid.uuid4().hex[:8]}"
    # Upload to S3 temp
    s3 = boto3.client("s3", region_name=AWS_REGION)
    bucket = os.getenv("TRANSCRIBE_BUCKET", "nam-sa-ghomala-training")
    key = f"temp-audio/{job_name}.wav"

    s3.put_object(Bucket=bucket, Key=key, Body=audio_bytes)
    s3_uri = f"s3://{bucket}/{key}"

    try:
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": s3_uri},
            MediaFormat="wav",
            LanguageCode="fr-FR",
        )
        # Poll for completion
        for _ in range(60):
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
            if job_status == "COMPLETED":
                import urllib.request
                result_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                with urllib.request.urlopen(result_url) as resp:
                    result = json.loads(resp.read())
                return result["results"]["transcripts"][0]["transcript"]
            elif job_status == "FAILED":
                return ""
            await asyncio.sleep(1)
        return ""
    finally:
        # Cleanup
        try:
            transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
        except Exception:
            pass
        try:
            s3.delete_object(Bucket=bucket, Key=key)
        except Exception:
            pass


async def synthesize_speech(text: str) -> bytes:
    """Convert text to speech using Amazon Polly."""
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat="pcm",
        VoiceId=POLLY_VOICE_ID,
        Engine=POLLY_ENGINE,
        SampleRate="24000",
    )
    return response["AudioStream"].read()


async def synthesize_speech_mp3(text: str, voice_id: str = "Lea") -> bytes:
    """Convert text to MP3 speech using Amazon Polly."""
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat="mp3",
        VoiceId=voice_id,
        Engine="neural",
    )
    return response["AudioStream"].read()


async def transcribe_audio_flexible(audio_bytes: bytes, media_format: str = "mp4") -> str:
    """
    Transcribe audio bytes to text using Amazon Transcribe (batch mode).
    Supports wav, mp4/m4a, mp3, flac, ogg, etc.
    """
    job_name = f"namsa-{uuid.uuid4().hex[:8]}"
    s3 = boto3.client("s3", region_name=AWS_REGION)
    bucket = os.getenv("TRANSCRIBE_BUCKET", "nam-sa-ghomala-training")
    ext = {"mp4": "m4a", "wav": "wav", "mp3": "mp3"}.get(media_format, "m4a")
    key = f"temp-audio/{job_name}.{ext}"

    s3.put_object(Bucket=bucket, Key=key, Body=audio_bytes)
    s3_uri = f"s3://{bucket}/{key}"

    try:
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={"MediaFileUri": s3_uri},
            MediaFormat=media_format,
            LanguageCode="fr-FR",
        )
        for _ in range(60):
            status = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = status["TranscriptionJob"]["TranscriptionJobStatus"]
            if job_status == "COMPLETED":
                import urllib.request
                result_url = status["TranscriptionJob"]["Transcript"]["TranscriptFileUri"]
                with urllib.request.urlopen(result_url) as resp:
                    result = json.loads(resp.read())
                return result["results"]["transcripts"][0]["transcript"]
            elif job_status == "FAILED":
                return ""
            await asyncio.sleep(1)
        return ""
    finally:
        try:
            transcribe_client.delete_transcription_job(TranscriptionJobName=job_name)
        except Exception:
            pass
        try:
            s3.delete_object(Bucket=bucket, Key=key)
        except Exception:
            pass


# ============================================================================
# WEBSOCKET — Voice Streaming
# ============================================================================
@app.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket):
    """
    Voice conversation via WebSocket.

    Protocol:
      Client → {"type": "config", "language": "fr", "mode": "tutor"}
      Client → {"type": "audio", "data": "<base64_pcm_16khz>"}
      Server → {"type": "transcript", "text": "...", "role": "user"|"assistant"}
      Server → {"type": "audio", "data": "<base64_pcm_24khz>"}
      Server → {"type": "status", "status": "ready|thinking|speaking|listening"}
      Client → {"type": "stop"}
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"Voice session started: {session_id}")

    config = {"language": "fr", "mode": "tutor"}

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg["type"] == "config":
                config.update(msg)
                await websocket.send_json({
                    "type": "status",
                    "status": "ready",
                    "session_id": session_id,
                })
                continue

            if msg["type"] == "audio":
                await websocket.send_json({"type": "status", "status": "thinking"})

                audio_bytes = base64.b64decode(msg["data"])

                try:
                    # Step 1: Speech → Text (Transcribe)
                    user_text = await transcribe_audio(audio_bytes)
                    if user_text:
                        await websocket.send_json({
                            "type": "transcript",
                            "text": user_text,
                            "role": "user",
                        })

                    # Step 2: Text → Response (Nova 2 Lite fine-tuned)
                    mode_instructions = {
                        "tutor": "L'utilisateur parle. Réponds comme un tuteur Ghomala' bienveillant.",
                        "conversation": "Continue la conversation en Ghomala'/Français.",
                        "proverb": "Partage un proverbe Bamiléké.",
                        "translate": "Traduis ce que l'utilisateur dit.",
                    }
                    instruction = mode_instructions.get(config.get("mode", "tutor"))
                    prompt = f"[Mode: {config.get('mode')}] {instruction}\n\nUtilisateur: {user_text or '[audio non transcrit]'}"
                    response_text = await call_nova_lite(prompt)

                    await websocket.send_json({
                        "type": "transcript",
                        "text": response_text,
                        "role": "assistant",
                    })

                    # Step 3: Response → Speech (Polly)
                    await websocket.send_json({"type": "status", "status": "speaking"})
                    audio_response = await synthesize_speech(response_text)
                    await websocket.send_json({
                        "type": "audio",
                        "data": base64.b64encode(audio_response).decode("utf-8"),
                        "format": "pcm",
                        "sample_rate": 24000,
                    })

                    await websocket.send_json({"type": "status", "status": "listening"})

                except Exception as e:
                    logger.error(f"Voice processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Erreur de traitement vocal. Réessaie.",
                    })

            if msg["type"] == "stop":
                break

    except WebSocketDisconnect:
        logger.info(f"Voice session ended: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


# ============================================================================
# WEBSOCKET — Live Voice Conversation (record-then-send)
# ============================================================================
@app.websocket("/ws/live")
async def live_voice_stream(websocket: WebSocket):
    """
    Live voice conversation via WebSocket (record-then-send pattern).
    Used by LiveScreen: records audio with silence detection, sends complete clips.

    Protocol:
      Client → {"type": "config", "language": "fr"}
      Server → {"type": "status", "status": "ready"}
      Client → {"type": "audio", "data": "<base64_m4a>", "mime_type": "audio/mp4"}
      Server → {"type": "user_transcript", "text": "..."}
      Server → {"type": "transcript", "text": "..."}     (assistant response)
      Server → {"type": "audio_response", "data": "<base64_mp3>", "format": "mp3"}
      Server → {"type": "turn_complete"}
      Server → {"type": "error", "message": "..."}
      Client → {"type": "stop"}
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"Live voice session started: {session_id}")

    config = {"language": "fr"}

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            if msg["type"] == "config":
                config.update(msg)
                await websocket.send_json({
                    "type": "status",
                    "status": "ready",
                    "session_id": session_id,
                })
                continue

            if msg["type"] == "audio":
                audio_bytes = base64.b64decode(msg["data"])
                mime_type = msg.get("mime_type", "audio/mp4")

                # Determine format for Transcribe
                media_format = "mp4"
                if "wav" in mime_type:
                    media_format = "wav"
                elif "mp3" in mime_type or "mpeg" in mime_type:
                    media_format = "mp3"

                try:
                    # Step 1: Speech → Text (Transcribe)
                    user_text = await transcribe_audio_flexible(audio_bytes, media_format)

                    if user_text:
                        await websocket.send_json({
                            "type": "user_transcript",
                            "text": user_text,
                        })

                    # Step 2: Text → Response (Nova 2 Lite fine-tuned)
                    prompt = (
                        f"[Mode: conversation] L'utilisateur parle. "
                        f"Réponds naturellement en Ghomala'/Français.\n\n"
                        f"Utilisateur: {user_text or '[audio non transcrit]'}"
                    )
                    response_text = await call_nova_lite(prompt)

                    await websocket.send_json({
                        "type": "transcript",
                        "text": response_text,
                    })

                    # Step 3: Response → Speech (Polly MP3)
                    audio_response = await synthesize_speech_mp3(response_text)
                    await websocket.send_json({
                        "type": "audio_response",
                        "data": base64.b64encode(audio_response).decode("utf-8"),
                        "format": "mp3",
                    })

                    # Signal turn complete so client can auto-restart listening
                    await websocket.send_json({"type": "turn_complete"})

                except Exception as e:
                    logger.error(f"Live voice processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Erreur de traitement vocal. Réessaie.",
                    })

            if msg["type"] == "stop":
                break

    except WebSocketDisconnect:
        logger.info(f"Live voice session ended: {session_id}")
    except Exception as e:
        logger.error(f"Live voice WebSocket error: {e}")


# ============================================================================
# NOVA 2 SONIC — Real-time Speech-to-Speech
# ============================================================================
class NovaSonicSession:
    """
    Manages a single bidirectional streaming session with Nova 2 Sonic.

    Lifecycle:
      start() → start_audio_input() → send_audio_chunk()* → end_audio_input() → end()
    Response events are yielded by process_responses() running concurrently.
    """

    def __init__(self, system_prompt: str, voice_id: str = NOVA_SONIC_VOICE_ID):
        self.system_prompt = system_prompt
        self.voice_id = voice_id
        self.stream = None
        self.is_active = False
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())

    async def start(self):
        """Start session: sessionStart → promptStart → system prompt."""
        # Refresh credentials from boto3 chain (handles ECS task role rotation)
        _sync_credentials_to_env()

        config = SonicConfig(
            endpoint_uri=f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com",
            region=AWS_REGION,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
        )
        client = SonicBedrockClient(config=config)

        self.stream = await client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(
                model_id=NOVA_SONIC_MODEL_ID
            )
        )
        self.is_active = True

        # 1. Session start
        await self._send({
            "event": {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "maxTokens": 1024,
                        "topP": 0.9,
                        "temperature": 0.7,
                    }
                }
            }
        })

        # 2. Prompt start with audio output config
        await self._send({
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 24000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "voiceId": self.voice_id,
                        "encoding": "base64",
                        "audioType": "SPEECH",
                    },
                }
            }
        })

        # 3. System prompt (TEXT content)
        await self._send({
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                    "type": "TEXT",
                    "interactive": False,
                    "role": "SYSTEM",
                    "textInputConfiguration": {"mediaType": "text/plain"},
                }
            }
        })
        await self._send({
            "event": {
                "textInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                    "content": self.system_prompt,
                }
            }
        })
        await self._send({
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                }
            }
        })

    async def start_audio_input(self):
        """Signal that user audio input is starting."""
        await self._send({
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 16000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "audioType": "SPEECH",
                        "encoding": "base64",
                    },
                }
            }
        })

    async def send_audio_chunk(self, audio_bytes: bytes):
        """Forward a chunk of raw PCM audio to Nova Sonic."""
        if not self.is_active:
            return
        blob = base64.b64encode(audio_bytes).decode("utf-8")
        await self._send({
            "event": {
                "audioInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "content": blob,
                }
            }
        })

    async def end_audio_input(self):
        """Signal end of user audio input."""
        await self._send({
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                }
            }
        })

    async def end(self):
        """End the session and close the stream."""
        if not self.is_active:
            return
        self.is_active = False
        try:
            await self._send({
                "event": {"promptEnd": {"promptName": self.prompt_name}}
            })
            await self._send({"event": {"sessionEnd": {}}})
            await self.stream.input_stream.close()
        except Exception:
            pass

    async def process_responses(self):
        """Async generator yielding events from Nova Sonic."""
        role = None
        display_text = False

        try:
            while self.is_active:
                output = await self.stream.await_output()
                result = await output[1].receive()

                if not (result.value and result.value.bytes_):
                    continue

                data = json.loads(result.value.bytes_.decode("utf-8"))
                if "event" not in data:
                    continue

                event = data["event"]

                if "contentStart" in event:
                    cs = event["contentStart"]
                    role = cs.get("role")
                    display_text = False
                    if "additionalModelFields" in cs:
                        extra = json.loads(cs["additionalModelFields"])
                        if extra.get("generationStage") == "SPECULATIVE":
                            display_text = True

                elif "textOutput" in event:
                    text = event["textOutput"]["content"]
                    if role == "ASSISTANT" and display_text:
                        yield {
                            "type": "transcript",
                            "text": text,
                            "role": "assistant",
                        }
                    elif role == "USER":
                        yield {
                            "type": "transcript",
                            "text": text,
                            "role": "user",
                        }

                elif "audioOutput" in event:
                    yield {
                        "type": "audio",
                        "data": event["audioOutput"]["content"],
                        "format": "pcm",
                        "sample_rate": 24000,
                    }

        except Exception as e:
            logger.error(f"Sonic response processing error: {e}")
            yield {"type": "error", "message": "Sonic stream error"}

    async def _send(self, event_dict: dict):
        """Send a JSON event to the bidirectional stream."""
        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(
                bytes_=json.dumps(event_dict).encode("utf-8")
            )
        )
        await self.stream.input_stream.send(event)


@app.websocket("/ws/sonic")
async def sonic_stream(websocket: WebSocket):
    """
    Real-time speech-to-speech via Nova 2 Sonic bidirectional streaming.

    Protocol:
      Client → {"type": "config", "mode": "tutor", "language": "fr"}   (optional)
      Client → {"type": "audio", "data": "<base64_pcm_16khz>"}         (audio chunks)
      Client → {"type": "stop"}                                        (end session)
      Server → {"type": "status", "status": "listening|error"}
      Server → {"type": "transcript", "text": "...", "role": "user|assistant"}
      Server → {"type": "audio", "data": "<base64_pcm_24khz>", "format": "pcm", "sample_rate": 24000}
      Server → {"type": "error", "message": "..."}
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"Sonic session started: {session_id}")

    session = NovaSonicSession(system_prompt=SYSTEM_PROMPT)

    try:
        await session.start()
        await session.start_audio_input()
        await websocket.send_json({
            "type": "status",
            "status": "listening",
            "session_id": session_id,
        })

        async def receive_from_mobile():
            """Receive audio chunks from mobile and forward to Sonic."""
            try:
                while session.is_active:
                    data = await websocket.receive_text()
                    msg = json.loads(data)
                    if msg["type"] == "audio":
                        audio_bytes = base64.b64decode(msg["data"])
                        await session.send_audio_chunk(audio_bytes)
                    elif msg["type"] == "stop":
                        await session.end_audio_input()
                        break
            except WebSocketDisconnect:
                pass

        async def relay_responses():
            """Relay Sonic responses back to mobile."""
            async for event in session.process_responses():
                try:
                    await websocket.send_json(event)
                except Exception:
                    break

        await asyncio.gather(
            receive_from_mobile(),
            relay_responses(),
        )

    except Exception as e:
        logger.error(f"Sonic session error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": "Sonic session failed"})
        except Exception:
            pass
    finally:
        await session.end()
        logger.info(f"Sonic session ended: {session_id}")


# ============================================================================
# ENTRY POINT
# ============================================================================
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
