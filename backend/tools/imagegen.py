"""generate_image and image_ai_edit: AI images made on this Mac with FLUX.2 Klein 4B (mflux).

Results go into the image store like any other image, so the canvas, versions,
image_edit and undo all work on them. An AI edit is a new version of the same image.
One run at a time (the model uses a lot of the Mac's memory).
Setup (Python, mflux, ~16 GB download, 8 GB kept): scripts/setup_images.sh
"""

import asyncio
import io
import logging
import os
import tempfile
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool
from PIL import Image

import config
from storage import image_store

from .images import _result, _show

log = logging.getLogger("jarvis.imagegen")

STEPS = 4  # Klein 4B is distilled for 4 steps
MAX_SIDE = 1024
SIZES = {"landscape": (1024, 768), "portrait": (768, 1024), "square": (1024, 1024)}
TIMEOUT_S = 10 * 60
CREDIT = {"source": "Generated on this Mac · FLUX.2 Klein"}

_lock = asyncio.Lock()


def model_dir() -> Path:
    return config.FLUX_DIR / "flux2-klein-4b-q8"


def _bin(name: str) -> Path:
    return config.FLUX_DIR / ".venv" / "bin" / name


def fit(width: int, height: int) -> tuple[int, int]:
    """The source's shape, at most MAX_SIDE on the long side, both sides multiples of 16."""
    scale = min(1.0, MAX_SIDE / max(width, height))
    return (max(16, round(width * scale / 16) * 16), max(16, round(height * scale / 16) * 16))


async def _flux(command: str, prompt: str, width: int, height: int, images: list[Path]) -> bytes:
    """Run one of mflux's commands and return the PNG it made."""
    if not _bin(command).exists() or not model_dir().is_dir():
        raise RuntimeError("image generation isn't set up on this Mac yet. The user needs to run "
                           "scripts/setup_images.sh once (it downloads about 16 GB)")
    async with _lock:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.png"
            args = ["--model", str(model_dir()), "--base-model", "flux2-klein-4b", "--prompt", prompt,
                    "--width", str(width), "--height", str(height), "--steps", str(STEPS),
                    "--no-metadata", "--output", str(out)]
            if images:
                args += ["--image-paths", *map(str, images)]
            proc = await asyncio.create_subprocess_exec(
                str(_bin(command)), *args,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
                env={**os.environ, "HF_HUB_OFFLINE": "1"},  # everything it needs is on disk
            )
            try:
                output, _ = await asyncio.wait_for(proc.communicate(), TIMEOUT_S)
            except TimeoutError:
                proc.kill()
                raise RuntimeError("the image model took too long") from None
            if proc.returncode != 0 or not out.exists():
                log.error("%s failed:\n%s", command, output.decode(errors="replace")[-3000:])
                raise RuntimeError("the image model failed (details in the backend log)")
            return out.read_bytes()


@tool(
    "generate_image",
    "Make a NEW picture with AI from a text description (FLUX.2 Klein, on this Mac, about "
    "20 seconds) and show it on the canvas. Use it when the user wants an image created, "
    "drawn or imagined; to find a real photo use image_search instead. Write the prompt in "
    "English as a detailed description: subject, setting, style (photo, illustration, "
    "watercolour, 3D render…), lighting, composition. Short text in quotes can be drawn. "
    "You get the result back to check.",
    {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Detailed English description of the image."},
            "title": {"type": "string", "description": "Short name, e.g. 'Fox in the snow'."},
            "orientation": {"type": "string", "enum": list(SIZES), "description": "Default landscape."},
        },
        "required": ["prompt"],
    },
)
async def generate_image(args: dict[str, Any]) -> dict[str, Any]:
    prompt = str(args.get("prompt") or "").strip()
    if not prompt:
        return _result("Not made: the prompt is empty.", is_error=True)
    width, height = SIZES.get(str(args.get("orientation") or "landscape"), SIZES["landscape"])
    try:
        data = await _flux("mflux-generate-flux2", prompt, width, height, [])
    except RuntimeError as e:
        return _result(f"Not made: {e}.", is_error=True)
    title = str(args.get("title") or prompt)[:80]
    rec = await asyncio.to_thread(image_store.create, title, data, CREDIT)
    await _show(rec)
    log.info("Generated %s: %r", rec.id, prompt)
    return _result(f"{rec.id}: {title!r}, {width}×{height}px, made with AI. Shown on the canvas.", rec)


@tool(
    "image_ai_edit",
    "Change an image on the canvas with AI, following an instruction in English (FLUX.2 "
    "Klein, on this Mac, about 30 seconds): e.g. 'make it snowy', 'turn it into a "
    "watercolour painting', 'put a red hat on the dog', 'remove the people in the background'. "
    "It keeps the image's shape and creates a new version (undo goes back). Pass up to 2 "
    "reference_ids of other images to combine things from them (e.g. 'put the glasses from "
    "the second image on the person'). For simple changes (crop, brightness, text, filters) "
    "use image_edit instead: it's exact and instant. You get the result back to check.",
    {
        "type": "object",
        "properties": {
            "image_id": {"type": "string", "description": "e.g. img_004"},
            "instruction": {"type": "string", "description": "What to change, in English."},
            "from_version": {"type": "integer", "description": "Edit this version instead of the current one."},
            "reference_ids": {"type": "array", "items": {"type": "string"}, "maxItems": 2},
        },
        "required": ["image_id", "instruction"],
    },
)
async def image_ai_edit(args: dict[str, Any]) -> dict[str, Any]:
    instruction = str(args.get("instruction") or "").strip()
    if not instruction:
        return _result("Not changed: the instruction is empty.", is_error=True)
    try:
        rec = image_store.load(str(args["image_id"]))
        base = rec.get(args.get("from_version"))
        refs = [image_store.load(str(r)) for r in (args.get("reference_ids") or [])[:2]]
        paths = [image_store.file_path(r.id, r.get(v).file) for r, v in [(rec, base.version), *((r, None) for r in refs)]]
        width, height = fit(base.width, base.height)
        data = await _flux("mflux-generate-flux2-edit", instruction, width, height, paths)
    except KeyError as e:
        return _result(f"Not changed: {str(e).strip(chr(39))}", is_error=True)
    except RuntimeError as e:
        return _result(f"Not changed: {e}.", is_error=True)
    img = Image.open(io.BytesIO(data))
    v = await asyncio.to_thread(image_store.add_version, rec, img, base.version, f"AI: {instruction}"[:120])
    await _show(rec)
    log.info("AI-edited %s v%s -> v%s: %r", rec.id, base.version, v.version, instruction)
    return _result(f"{rec.id} v{v.version}: AI edit “{instruction}”. Shown on the canvas.", rec)
