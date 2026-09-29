"""generate_video: short AI videos made on this Mac with Wan 2.1 (1.3B) through mlx-video.

A 5 s video takes ~13 minutes on an M5, so the tool starts the job in the background and returns right
away: the canvas card shows progress and then the video, and the chat stays free.
One video at a time (the model uses most of the Mac while it runs).
Setup (Python, mlx-video, ~17 GB of weights): scripts/setup_video.sh
"""

import asyncio
import logging
import re
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool

import config
import events
import hub
from storage import video_store

log = logging.getLogger("jarvis.video")

FPS = 16  # Wan 2.1's frame rate
WIDTH, HEIGHT = 832, 480  # the 1.3B model is trained for 480p
MAX_SECONDS = 5
STEPS = {"fast": 10, "best": 20}  # ~67 s per step for a 5 s clip on an M5
TIMEOUT_S = 60 * 60
_PROGRESS = re.compile(rb"Diffusion:[^|]*\|[^|]*\|\s*(\d+)/(\d+)")

_job: asyncio.Task | None = None


def python() -> Path:
    return config.WAN_DIR / ".venv" / "bin" / "python"


def model_dir() -> Path:
    return config.WAN_DIR / "Wan2.1-T2V-1.3B-MLX"


def frames_for(seconds: float) -> int:
    """Wan needs 4n+1 frames: 5 s -> 81 frames at 16 fps."""
    seconds = min(max(seconds, 1.0), MAX_SECONDS)
    return 4 * max(1, round(seconds * FPS / 4)) + 1


def last_progress(output: bytes) -> tuple[int, int] | None:
    """The latest 'Diffusion: 40%|███ | 12/30' tqdm step in a chunk of output."""
    found = _PROGRESS.findall(output)
    return (int(found[-1][0]), int(found[-1][1])) if found else None


def _text(text: str, is_error: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        out["is_error"] = True
    return out


async def _show(rec: video_store.VideoRecord) -> None:
    await asyncio.to_thread(video_store.save, rec)
    await hub.emit(events.canvas_card(rec.id, "video", rec.title, video_store.card_data(rec)))


async def _render(rec: video_store.VideoRecord, frames: int, steps: int) -> None:
    out = video_store.folder(rec.id) / "rendering.mp4"
    proc = await asyncio.create_subprocess_exec(
        str(python()), "-m", "mlx_video.models.wan_2.generate",
        "--model-dir", str(model_dir()), "--prompt", rec.prompt,
        "--width", str(WIDTH), "--height", str(HEIGHT), "--num-frames", str(frames),
        "--steps", str(steps), "--output-path", str(out),
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    tail = b""
    try:
        async with asyncio.timeout(TIMEOUT_S):
            while chunk := await proc.stdout.read(4096):
                tail = (tail + chunk)[-4000:]
                step = last_progress(chunk)
                if step and step[0] / step[1] > rec.progress:
                    rec.progress = step[0] / step[1]
                    await _show(rec)
            await proc.wait()
        if proc.returncode != 0 or not out.exists():
            log.error("Video %s failed:\n%s", rec.id, tail.decode(errors="replace"))
            raise RuntimeError("the video model failed (details in the backend log)")
        out.rename(out.with_name(video_store.FILE))
        rec.status, rec.progress = "done", 1.0
        await _show(rec)
        await hub.emit(events.notice(f"Your video “{rec.title}” is ready on the canvas."))
    except (Exception, asyncio.CancelledError) as e:
        if proc.returncode is None:
            proc.kill()
        rec.status = "failed"
        rec.error = "It took too long." if isinstance(e, TimeoutError) else f"Couldn't make it: {e}"
        log.exception("Video %s failed", rec.id)
        await _show(rec)
        if isinstance(e, asyncio.CancelledError):
            raise


@tool(
    "generate_video",
    "Make a short AI video (1–5 seconds, 832×480, no sound) from a text description, on this Mac "
    "with the Wan 2.1 model. It is slow: about 13 minutes for 5 seconds on fast (shorter clips are "
    "quicker). This starts it and returns right away; the "
    "canvas shows progress and then the video. One video at a time. The user confirms first. "
    "Write the prompt in English, as one detailed shot: subject, action, setting, camera "
    "(e.g. slow dolly-in, close-up), lighting and style. The model is small: simple scenes with "
    "one clear subject and motion work best; readable text, hands and crowds come out poorly.",
    {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Detailed English description of the shot."},
            "title": {"type": "string", "description": "Short name, e.g. 'Cat on a piano'."},
            "seconds": {"type": "number", "description": f"Length, 1–{MAX_SECONDS} (default 5)."},
            "quality": {
                "type": "string",
                "enum": list(STEPS),
                "description": "fast (default) or best (about twice as long, more detail).",
            },
        },
        "required": ["prompt"],
    },
)
async def generate_video(args: dict[str, Any]) -> dict[str, Any]:
    global _job
    prompt = str(args.get("prompt") or "").strip()
    if not prompt:
        return _text("Not started: the prompt is empty.", is_error=True)
    if not python().exists() or not (model_dir() / "config.json").exists():
        return _text("Video generation isn't set up on this Mac yet. The user needs to run "
                     "scripts/setup_video.sh once (it downloads about 17 GB).", is_error=True)
    if _job and not _job.done():
        return _text("Another video is still being made; wait until it's finished.", is_error=True)

    frames = frames_for(float(args.get("seconds") or MAX_SECONDS))
    steps = STEPS.get(str(args.get("quality") or "fast"), STEPS["fast"])
    title = str(args.get("title") or prompt[:40])
    rec = await asyncio.to_thread(video_store.create, title, prompt, round(frames / FPS, 1), WIDTH, HEIGHT)
    await _show(rec)
    # ponytail: the job lives in this process; a backend restart mid-render leaves the card "rendering"
    _job = asyncio.create_task(_render(rec, frames, steps))
    log.info("Video %s started: %s frames, %s steps", rec.id, frames, steps)
    return _text(f"{rec.id} has started ({rec.seconds} s, {steps} steps). A 5 s clip takes about 13 minutes on fast; the canvas shows "
                 "progress and plays the video when it's done. Tell the user briefly; don't wait for it.")
