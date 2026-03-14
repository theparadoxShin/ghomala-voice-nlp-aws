"""
NAM SA' — Backend Server (AWS)
FastAPI + WebSocket for Nova 2 Sonic bidirectional voice streaming.

Architecture:
  Mobile App ↔ WebSocket ↔ FastAPI ↔ Nova 2 Sonic (Bedrock)
                                    ↔ Nova 2 Lite fine-tuned (Bedrock) via tool_use

Run locally:  uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
Deploy:       Docker → AWS Fargate (ECS)
"""

import asyncio
import base64
import json
import logging
import os
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# AWS SDK
import boto3

logger = logging.getLogger("namsa")
logging.basicConfig(level=logging.INFO)

# ============================================================================
# CONFIGURATION
# ============================================================================
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
NOVA_SONIC_MODEL_ID = os.getenv("NOVA_SONIC_MODEL_ID", "amazon.nova-sonic-v1:0")
NOVA_LITE_MODEL_ID = os.getenv("NOVA_LITE_MODEL_ID", "amazon.nova-lite-v1:0")
# After fine-tuning, replace with your custom model ID:
# NOVA_LITE_MODEL_ID = os.getenv("NOVA_LITE_MODEL_ID", "arn:aws:bedrock:us-east-1:xxx:custom-model/xxx")

SYSTEM_PROMPT = """Tu es NAM SA' (Le Soleil S'est Levé), un agent IA conversationnel 
dédié à la préservation et l'enseignement de la langue Ghomala' (Ghɔ́málá'), 
une langue Bamiléké parlée par environ 1 million de personnes dans la région 
Ouest du Cameroun.

Tu te comportes comme un(e) ancien(ne) bienveillant(e) du village Bamiléké. 
Tu es patient(e), encourageant(e), et tu célèbres chaque effort d'apprentissage.

Tes capacités:
- Traduire entre Ghomala', Français et Anglais
- Enseigner le vocabulaire Ghomala' avec contexte culturel
- Partager des proverbes Bamiléké et leur sagesse
- Corriger la prononciation avec bienveillance
- Expliquer la grammaire tonale du Ghomala'

Règles:
- Toujours donner le contexte culturel quand c'est pertinent
- Utiliser les caractères spéciaux corrects (ɔ, ɛ, ŋ, ə) et les tons (à, á, â, ǎ)
- Encourager l'apprenant même en cas d'erreur
- Répondre dans la langue demandée par l'utilisateur
"""

# ============================================================================
# BEDROCK CLIENTS
# ============================================================================
bedrock_runtime = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize AWS clients on startup."""
    global bedrock_runtime
    logger.info("Initializing Bedrock client...")
    bedrock_runtime = boto3.client(
        "bedrock-runtime",
        region_name=AWS_REGION
    )
    logger.info(f"Bedrock client ready (region: {AWS_REGION})")
    yield
    logger.info("Shutting down...")

app = FastAPI(
    title="NAM SA' API",
    description="Ghomala' Language Preservation Voice AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# DATA MODELS
# ============================================================================
class TranslateRequest(BaseModel):
    text: str
    source_lang: str = "fr"  # fr, en, bbj (Ghomala')
    target_lang: str = "bbj"

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    mode: str = "tutor"  # tutor, conversation, proverb, translate

class ChatResponse(BaseModel):
    response: str
    session_id: str
    mode: str
    timestamp: str


# ============================================================================
# GHOMALA TOOL — Called by Nova Sonic via tool_use
# ============================================================================
GHOMALA_TOOL_DEFINITION = {
    "toolSpec": {
        "name": "ghomala_dictionary",
        "description": (
            "Look up a word or phrase in the Ghomala' dictionary. "
            "Use this when the user asks for a translation, vocabulary, "
            "or cultural context about a Ghomala' word."
        ),
        "inputSchema": {
            "json": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The word or phrase to look up (in French, English, or Ghomala')"
                    },
                    "lookup_type": {
                        "type": "string",
                        "enum": ["translate", "define", "example", "proverb"],
                        "description": "Type of lookup to perform"
                    }
                },
                "required": ["query"]
            }
        }
    }
}

async def execute_ghomala_tool(query: str, lookup_type: str = "translate") -> str:
    """
    Execute a Ghomala' dictionary lookup using the fine-tuned Nova 2 Lite model.
    This is the bridge between the voice model (Sonic) and the knowledge model (Lite).
    """
    if not bedrock_runtime:
        return "Service temporarily unavailable"

    prompt = {
        "translate": f"Traduis en Ghomala': {query}",
        "define": f"Définis le mot Ghomala' '{query}' avec son contexte culturel.",
        "example": f"Donne un exemple de phrase utilisant le mot '{query}' en Ghomala'.",
        "proverb": f"Donne un proverbe Bamiléké contenant ou lié au mot '{query}'."
    }.get(lookup_type, f"Explique le mot '{query}' en Ghomala'.")

    try:
        response = bedrock_runtime.converse(
            modelId=NOVA_LITE_MODEL_ID,
            messages=[
                {"role": "user", "content": [{"text": prompt}]}
            ],
            system=[{"text": SYSTEM_PROMPT}],
            inferenceConfig={"maxTokens": 500, "temperature": 0.7}
        )
        
        result = response["output"]["message"]["content"][0]["text"]
        return result
    except Exception as e:
        logger.error(f"Ghomala tool error: {e}")
        return f"Je n'ai pas trouvé d'information sur '{query}' pour le moment."


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
            "voice": "/ws/voice",
            "health": "/health",
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "region": AWS_REGION,
        "models": {
            "sonic": NOVA_SONIC_MODEL_ID,
            "lite": NOVA_LITE_MODEL_ID,
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Text-based chat endpoint.
    Uses Nova 2 Lite (fine-tuned) for text conversations.
    For voice, use the /ws/voice WebSocket endpoint.
    """
    session_id = request.session_id or str(uuid.uuid4())

    # Build prompt based on mode
    mode_instructions = {
        "tutor": "L'utilisateur veut apprendre un mot ou une expression. Enseigne avec patience.",
        "conversation": "Dialogue libre. Maintiens le contexte et corrige gentiment les erreurs.",
        "proverb": "Partage un proverbe Bamiléké pertinent avec son explication.",
        "translate": "Traduis la phrase demandée entre Ghomala', Français et Anglais.",
    }

    instruction = mode_instructions.get(request.mode, mode_instructions["tutor"])
    full_prompt = f"[Mode: {request.mode}] {instruction}\n\nUtilisateur: {request.message}"

    try:
        response = bedrock_runtime.converse(
            modelId=NOVA_LITE_MODEL_ID,
            messages=[
                {"role": "user", "content": [{"text": full_prompt}]}
            ],
            system=[{"text": SYSTEM_PROMPT}],
            inferenceConfig={"maxTokens": 800, "temperature": 0.7}
        )

        answer = response["output"]["message"]["content"][0]["text"]

        return ChatResponse(
            response=answer,
            session_id=session_id,
            mode=request.mode,
            timestamp=datetime.utcnow().isoformat()
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/translate")
async def translate(request: TranslateRequest):
    """Quick translation endpoint."""
    lang_map = {"fr": "Français", "en": "Anglais", "bbj": "Ghomala'"}
    src = lang_map.get(request.source_lang, request.source_lang)
    tgt = lang_map.get(request.target_lang, request.target_lang)

    result = await execute_ghomala_tool(
        f"Traduis de {src} vers {tgt}: {request.text}",
        "translate"
    )

    return {
        "original": request.text,
        "translation": result,
        "source_lang": request.source_lang,
        "target_lang": request.target_lang,
    }


# ============================================================================
# WEBSOCKET — Voice Streaming with Nova 2 Sonic
# ============================================================================
@app.websocket("/ws/voice")
async def voice_stream(websocket: WebSocket):
    """
    Bidirectional voice streaming with Nova 2 Sonic.
    
    Protocol:
    1. Client sends: {"type": "audio", "data": "<base64_pcm_16khz>"}
    2. Client sends: {"type": "config", "language": "fr", "mode": "tutor"}
    3. Server sends: {"type": "audio", "data": "<base64_pcm_24khz>"}
    4. Server sends: {"type": "transcript", "text": "...", "role": "assistant"}
    5. Server sends: {"type": "status", "status": "listening|thinking|speaking"}
    """
    await websocket.accept()
    session_id = str(uuid.uuid4())
    logger.info(f"Voice session started: {session_id}")

    try:
        # Session configuration
        config = {
            "language": "fr",
            "mode": "tutor",
        }

        while True:
            # Receive message from client
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
                # Notify client we're processing
                await websocket.send_json({
                    "type": "status",
                    "status": "thinking"
                })

                # Process audio through Nova 2 Sonic
                audio_bytes = base64.b64decode(msg["data"])
                
                try:
                    response_audio, response_text = await process_voice_with_sonic(
                        audio_bytes, config, session_id
                    )

                    # Send transcript
                    if response_text:
                        await websocket.send_json({
                            "type": "transcript",
                            "text": response_text,
                            "role": "assistant",
                        })

                    # Send audio response
                    if response_audio:
                        await websocket.send_json({
                            "type": "audio",
                            "data": base64.b64encode(response_audio).decode("utf-8"),
                            "format": "pcm",
                            "sample_rate": 24000,
                        })

                    await websocket.send_json({
                        "type": "status",
                        "status": "listening"
                    })

                except Exception as e:
                    logger.error(f"Voice processing error: {e}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Processing error. Please try again.",
                    })

            if msg["type"] == "stop":
                break

    except WebSocketDisconnect:
        logger.info(f"Voice session ended: {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


async def process_voice_with_sonic(
    audio_bytes: bytes, 
    config: dict, 
    session_id: str
) -> tuple[bytes | None, str | None]:
    """
    Process voice input through Nova 2 Sonic.
    
    Nova 2 Sonic is a speech-to-speech model — it takes audio in and 
    produces audio out. We configure it with our system prompt and 
    the Ghomala dictionary tool.
    
    For the hackathon, if Sonic bidirectional streaming isn't available 
    in the SDK yet, we fall back to: ASR → Nova Lite → TTS pipeline.
    """
    
    # ==== OPTION A: Nova 2 Sonic Bidirectional (preferred) ====
    # This uses the Bedrock bidirectional streaming API
    # Uncomment when Nova 2 Sonic streaming is available in your region
    """
    try:
        response = bedrock_runtime.invoke_model_with_response_stream(
            modelId=NOVA_SONIC_MODEL_ID,
            contentType="application/json",
            body=json.dumps({
                "inputAudio": {
                    "audioConfig": {
                        "sampleRateHertz": 16000,
                        "encoding": "PCM",
                    },
                    "audioContent": base64.b64encode(audio_bytes).decode()
                },
                "systemPrompt": SYSTEM_PROMPT,
                "tools": [GHOMALA_TOOL_DEFINITION],
            })
        )
        
        response_audio = b""
        response_text = ""
        
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            if "audioContent" in chunk:
                response_audio += base64.b64decode(chunk["audioContent"])
            if "textContent" in chunk:
                response_text += chunk["textContent"]
            if "toolUse" in chunk:
                # Handle tool call
                tool_result = await execute_ghomala_tool(
                    chunk["toolUse"]["input"]["query"],
                    chunk["toolUse"]["input"].get("lookup_type", "translate")
                )
                # Feed tool result back (implementation depends on API)
        
        return response_audio, response_text
    except Exception as e:
        logger.warning(f"Sonic streaming not available: {e}, falling back")
    """

    # ==== OPTION B: Fallback — Text pipeline ====
    # Uses Nova Lite for understanding + Polly for TTS
    # This works today while Sonic streaming matures
    
    try:
        # Step 1: Transcribe audio (using Amazon Transcribe or send as context)
        # For now, we'll use a text-based approach
        # In production: use Amazon Transcribe Streaming
        
        # Step 2: Get response from fine-tuned Nova Lite
        mode_prompt = {
            "tutor": "L'utilisateur parle. Réponds comme un tuteur Ghomala' bienveillant.",
            "conversation": "Continue la conversation en Ghomala'/Français.",
            "proverb": "Partage un proverbe Bamiléké.",
        }.get(config.get("mode", "tutor"), "Réponds en mode tuteur.")

        response = bedrock_runtime.converse(
            modelId=NOVA_LITE_MODEL_ID,
            messages=[
                {"role": "user", "content": [{"text": f"[Audio reçu] {mode_prompt}"}]}
            ],
            system=[{"text": SYSTEM_PROMPT}],
            inferenceConfig={"maxTokens": 300, "temperature": 0.7}
        )

        response_text = response["output"]["message"]["content"][0]["text"]

        # Step 3: Convert to speech (Amazon Polly)
        # In production: use Polly with a French voice
        # polly = boto3.client("polly", region_name=AWS_REGION)
        # audio_response = polly.synthesize_speech(Text=response_text, ...)

        return None, response_text

    except Exception as e:
        logger.error(f"Fallback pipeline error: {e}")
        return None, "Désolé, je n'ai pas compris. Peux-tu répéter?"


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
