"""FastAPI app + /ws WebSocket, bound to 127.0.0.1.

Run from the backend folder:
    .venv/bin/python main.py
"""

import asyncio
import json
import logging
from contextlib import aclosing, asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

import config
import events
import hub
from brain.agent import Jarvis
from brain.base import ModelAlias
from brain.brain_claudecode import ClaudeCodeBrain
from brain.confirm import ConfirmationGate
from storage import image_store

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
gate = ConfirmationGate()
brain = ClaudeCodeBrain(can_use_tool=gate.can_use_tool)
jarvis = Jarvis(brain)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config.use_pro_login()
    warm_up = asyncio.create_task(brain.start())  # ready before your first message
    yield
    warm_up.cancel()
    await brain.close()


app = FastAPI(title="Jarvis", lifespan=lifespan)


@app.get("/health")
async def health() -> dict:
    return {"ok": True, "auth": brain.auth_source}


@app.get("/assets/{image_id}/{filename}")
async def asset(image_id: str, filename: str, download: bool = False) -> FileResponse:
    """Image files for the canvas. Names are checked strictly, so only stored images can be read."""
    try:
        path = image_store.file_path(image_id, filename)
    except KeyError:
        raise HTTPException(404) from None
    if download:
        return FileResponse(path, media_type="image/jpeg", filename=f"{image_id}_{filename}")
    return FileResponse(path, media_type="image/jpeg", headers={"Cache-Control": "max-age=31536000, immutable"})


def make_sender(ws: WebSocket) -> hub.Sender:
    """Send JSON to one tab. The lock stops a reply and a hub event (e.g. a
    confirmation card) from being written to the socket at the same moment."""
    lock = asyncio.Lock()

    async def send(event: events.Event) -> None:
        async with lock:
            await ws.send_json(event)

    return send


async def run_turn(
    send: hub.Sender, text: str, model_override: ModelAlias | None, selected_image: dict | None
) -> None:
    """Answer one user message and stream the reply to the browser."""
    await send(events.status("thinking"))
    try:
        # aclosing: if sending fails (browser gone), end the brain turn right away.
        async with aclosing(jarvis.handle_text(text, model_override, selected_image=selected_image)) as stream:
            async for ev in stream:
                await send(ev)
    finally:
        try:
            await send(events.status("idle"))
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
    send = make_sender(ws)
    hub.connect(send)
    for request in gate.pending_requests():  # questions asked before this tab opened
        await send(request)
    model_override: ModelAlias | None = None
    selected_image: dict | None = None  # the image you clicked on the canvas
    turns: set[asyncio.Task] = set()

    try:
        while True:
            try:
                msg = json.loads(await ws.receive_text())
                kind = msg["type"]
            except (json.JSONDecodeError, KeyError, TypeError):
                await send(events.error("Invalid message"))
                continue

            if kind == "user.text":
                text = str(msg.get("text", "")).strip()
                if not text:
                    continue
                # Run the turn in the background so this loop keeps listening
                # (later: confirmations, barge-in). The brain runs one turn at a time.
                task = asyncio.create_task(run_turn(send, text, model_override, selected_image))
                turns.add(task)
                task.add_done_callback(turns.discard)

            elif kind == "user.confirm":
                if not gate.resolve(str(msg.get("id")), msg.get("approved") is True):
                    await send(events.error("That confirmation is no longer waiting."))

            elif kind == "user.select_image":
                image_id, version = msg.get("id"), msg.get("version")
                if image_id is None:
                    selected_image = None
                elif image_store.IMAGE_ID.match(str(image_id)) and isinstance(version, int):
                    selected_image = {"id": str(image_id), "version": version}
                else:
                    await send(events.error("Invalid image selection"))

            elif kind == "settings.update":
                override = msg.get("model_override")
                if override is None or override in MODELS:
                    model_override = override
                else:
                    await send(events.error(f"Unknown model: {override}"))

            else:
                await send(events.error(f"Unknown message type: {kind}"))

    except WebSocketDisconnect:
        log.info("Browser disconnected")
    finally:
        hub.disconnect(send)
        for task in turns:
            task.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host=config.HOST, port=config.PORT)
