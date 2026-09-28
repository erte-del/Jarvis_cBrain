"""FastAPI app + /ws WebSocket, bound to 127.0.0.1.

Run from the backend folder:
    .venv/bin/python main.py
"""

import asyncio
import json
import logging
import uuid
from contextlib import aclosing, asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

import config
import events
from brain.base import ModelAlias
from brain.brain_claudecode import ClaudeCodeBrain

log = logging.getLogger("jarvis")

# Only Jarvis's own frontend may connect. Without this check, any website open
# in your browser could talk to ws://127.0.0.1:8000 and use Jarvis.
ALLOWED_ORIGINS = {
    "http://127.0.0.1:5173",
    "http://localhost:5173",
}

MODELS: set[str] = {"haiku", "sonnet", "opus"}

# One brain for the whole app: Jarvis has one user and one ongoing conversation,
# shared by every open tab (and later by voice).
brain = ClaudeCodeBrain()


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.use_pro_login()
    yield
    await brain.close()


app = FastAPI(title="Jarvis", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "auth": brain.auth_source}


async def run_turn(ws: WebSocket, text: str, model: ModelAlias) -> None:
    """Send one user message to the brain and stream the reply to the browser."""
    reply_id = uuid.uuid4().hex[:12]
    await ws.send_json(events.status("thinking"))
    try:
        # aclosing: if sending fails (browser gone), end the brain turn right away.
        async with aclosing(brain.send(text, model=model)) as stream:
            async for ev in stream:
                await ws.send_json(events.from_brain(ev, reply_id))
    finally:
        try:
            await ws.send_json(events.status("idle"))
        except Exception:
            pass  # browser already gone


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    origin = ws.headers.get("origin")
    if origin not in ALLOWED_ORIGINS:
        log.warning("Rejected WebSocket from origin %r", origin)
        await ws.close(code=1008)  # policy violation
        return

    await ws.accept()
    log.info("Browser connected")
    model_override: ModelAlias | None = None
    turns: set[asyncio.Task] = set()

    try:
        while True:
            try:
                msg = json.loads(await ws.receive_text())
                kind = msg["type"]
            except (json.JSONDecodeError, KeyError, TypeError):
                await ws.send_json(events.error("Invalid message"))
                continue

            if kind == "user.text":
                text = str(msg.get("text", "")).strip()
                if not text:
                    continue
                # Phase 2 replaces this with the router.
                model: ModelAlias = model_override or "sonnet"
                # Run the turn in the background so this loop keeps listening
                # (later: confirmations, barge-in). The brain runs one turn at a time.
                task = asyncio.create_task(run_turn(ws, text, model))
                turns.add(task)
                task.add_done_callback(turns.discard)

            elif kind == "settings.update":
                override = msg.get("model_override")
                if override is None or override in MODELS:
                    model_override = override
                else:
                    await ws.send_json(events.error(f"Unknown model: {override}"))

            else:
                await ws.send_json(events.error(f"Unknown message type: {kind}"))

    except WebSocketDisconnect:
        log.info("Browser disconnected")
    finally:
        for task in turns:
            task.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
