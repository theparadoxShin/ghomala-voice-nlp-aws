"""Test Nova 2 Sonic WebSocket endpoint."""
import asyncio
import json
import base64
import websockets

async def test_sonic():
    uri = "ws://localhost:8000/ws/sonic"
    print("Connecting to Sonic endpoint...")

    try:
        async with websockets.connect(uri) as ws:
            # Wait for initial status
            resp = await asyncio.wait_for(ws.recv(), timeout=15)
            data = json.loads(resp)
            print(f"Initial response: {data}")

            if data.get("type") == "status" and data.get("status") == "listening":
                print("Sonic session ACTIVE - ready for audio input")

                # Send a small silent audio chunk (PCM 16kHz, 16-bit, mono)
                # 0.5 seconds of silence = 16000 samples/s * 0.5s * 2 bytes = 16000 bytes
                silence = b'\x00' * 16000
                await ws.send(json.dumps({
                    "type": "audio",
                    "data": base64.b64encode(silence).decode()
                }))
                print("Sent 0.5s of silence")

                # Send stop
                await ws.send(json.dumps({"type": "stop"}))
                print("Sent stop signal")

                # Collect any responses for a few seconds
                try:
                    while True:
                        resp = await asyncio.wait_for(ws.recv(), timeout=5)
                        data = json.loads(resp)
                        if data.get("type") == "transcript":
                            print(f"  Transcript ({data.get('role')}): {data.get('text', '')[:100]}")
                        elif data.get("type") == "audio":
                            audio_len = len(base64.b64decode(data["data"]))
                            print(f"  Audio response: {audio_len} bytes")
                        elif data.get("type") == "error":
                            print(f"  Error: {data.get('message')}")
                        else:
                            print(f"  Event: {data}")
                except asyncio.TimeoutError:
                    print("No more responses (timeout)")

            print("\nSonic endpoint test PASSED")

    except Exception as e:
        print(f"Sonic test error: {e}")
        import traceback
        traceback.print_exc()

asyncio.run(test_sonic())
