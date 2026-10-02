"""image_search, image_edit, image versions. (Phase 4c)

Photos come from Pexels (free API key in .env). Edits run locally with Pillow and
every edit is a new version, so nothing is ever lost. Each tool shows the result on
the canvas and hands Claude a small copy so it can see what it found or made.
"""

import asyncio
import base64
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

from claude_agent_sdk import tool

import config
import events
import hub
from storage import image_store

from .image_ops import OPERATIONS, EditError, apply_all

log = logging.getLogger("jarvis.images")

PEXELS_SEARCH = "https://api.pexels.com/v1/search"
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024


# ---- Pexels -----------------------------------------------------------------------

def _http_get(url: str, headers: dict[str, str]) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/0.1", **headers})
    with urllib.request.urlopen(req, timeout=20, context=config.ssl_context()) as r:
        data = r.read(MAX_DOWNLOAD_BYTES + 1)
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise RuntimeError("image too large")
    return data


def _pexels_search(query: str, count: int, orientation: str | None) -> list[dict[str, Any]]:
    if not config.PEXELS_API_KEY:
        raise RuntimeError("No PEXELS_API_KEY in .env")
    params = {"query": query, "per_page": count}
    if orientation:
        params["orientation"] = orientation
    raw = _http_get(f"{PEXELS_SEARCH}?{urllib.parse.urlencode(params)}", {"Authorization": config.PEXELS_API_KEY})
    return json.loads(raw).get("photos", [])


def _download(photo: dict[str, Any]) -> bytes:
    url = photo["src"].get("large2x") or photo["src"]["large"]
    host = urllib.parse.urlparse(url).hostname or ""
    if not host.endswith("pexels.com"):  # only ever fetch Pexels' own image servers
        raise RuntimeError(f"unexpected image host {host}")
    return _http_get(url, {})


# ---- Helpers ------------------------------------------------------------------------

def _result(text: str, rec: image_store.ImageRecord | None = None, is_error: bool = False) -> dict[str, Any]:
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    if rec is not None:  # let Claude see the image
        data = base64.b64encode(image_store.preview_jpeg(rec)).decode()
        content.append({"type": "image", "data": data, "mimeType": "image/jpeg"})
    out: dict[str, Any] = {"content": content}
    if is_error:
        out["is_error"] = True
    return out


async def _show(rec: image_store.ImageRecord) -> None:
    await hub.emit(events.canvas_card(rec.id, "image", rec.title, image_store.card_data(rec)))


def _load(image_id: str) -> image_store.ImageRecord:
    try:
        return image_store.load(str(image_id))
    except KeyError as e:
        raise EditError(str(e).strip("'\"")) from None


# ---- Tools --------------------------------------------------------------------------

@tool(
    "image_search",
    "Find a photo on Pexels and show it on the canvas. You get a small copy back so you "
    "can check it matches the request. Returns the image id (e.g. img_004) for later edits.",
    {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What the photo should show, in English."},
            "count": {"type": "integer", "minimum": 1, "maximum": 4, "description": "How many photos (default 1)."},
            "orientation": {"type": "string", "enum": ["landscape", "portrait", "square"]},
        },
        "required": ["query"],
    },
)
async def image_search(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args["query"]).strip()
    count = int(args.get("count") or 1)
    try:
        photos = await asyncio.to_thread(_pexels_search, query, count, args.get("orientation"))
    except (urllib.error.URLError, RuntimeError, json.JSONDecodeError) as e:
        log.warning("Pexels search failed: %s", e)
        return _result(f"Image search failed: {e}", is_error=True)
    if not photos:
        return _result(f"No photos found for {query!r}. Try different words.", is_error=True)

    content: list[dict[str, Any]] = []
    for photo in photos[:count]:
        try:
            data = await asyncio.to_thread(_download, photo)
        except (urllib.error.URLError, RuntimeError, KeyError) as e:
            log.warning("Download failed: %s", e)
            continue
        credit = {
            "photographer": str(photo.get("photographer") or ""),
            "photographer_url": str(photo.get("photographer_url") or ""),
            "source_url": str(photo.get("url") or ""),
            "source": "Pexels",
        }
        title = str(photo.get("alt") or query).strip()[:80] or query
        rec = await asyncio.to_thread(image_store.create, title, data, credit)
        await _show(rec)
        log.info("Found %s for %r", rec.id, query)
        v = rec.get()
        content += _result(
            f"{rec.id}: {title!r}, {v.width}×{v.height}px, photo by {credit['photographer']} on Pexels. "
            "Shown on the canvas.",
            rec,
        )["content"]

    if not content:
        return _result("Found photos but couldn't download them. Try again.", is_error=True)
    return {"content": content}


@tool(
    "image_edit",
    "Edit an image on the canvas. Operations run in order and create a new version "
    "(the old one is kept, so it can be undone). Positions and sizes are fractions 0–1. "
    "Operations: "
    "crop {left,top,right,bottom} or {aspect:'16:9'}; "
    "resize {scale} or {width,height} px; "
    "rotate {degrees} (positive = clockwise, optional fill color); "
    "flip {direction: horizontal|vertical}; "
    "brightness|contrast|saturation {factor} (1 = unchanged, 0.5 = half, 1.5 = more); "
    "sharpen {factor}; blur {radius} px; grayscale {}; sepia {}; "
    "add_text {text, position: top|center|bottom|top-left|top-right|bottom-left|bottom-right, "
    "size (fraction of height, default 0.08), color, outline (bool)}; "
    "add_border {width (fraction of shorter side, default 0.03), color}. "
    "You get the result back to check it.",
    {
        "type": "object",
        "properties": {
            "image_id": {"type": "string", "description": "e.g. img_004"},
            "operations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"op": {"type": "string", "enum": sorted(OPERATIONS)}},
                    "required": ["op"],
                },
            },
            "from_version": {
                "type": "integer",
                "description": "Edit this version instead of the current one (e.g. to branch from v1).",
            },
        },
        "required": ["image_id", "operations"],
    },
)
async def image_edit(args: dict[str, Any]) -> dict[str, Any]:
    try:
        rec = _load(args["image_id"])
        base = rec.get(args.get("from_version"))
        img = image_store.open_version(rec, base.version)
        edited, note = await asyncio.to_thread(apply_all, img, args.get("operations") or [])
    except (EditError, KeyError) as e:
        return _result(f"Edit not done: {e}", is_error=True)
    v = await asyncio.to_thread(image_store.add_version, rec, edited, base.version, note)
    await _show(rec)
    log.info("Edited %s v%s -> v%s: %s", rec.id, base.version, v.version, note)
    return _result(f"{rec.id} v{v.version} ({v.width}×{v.height}px): {note}. Shown on the canvas.", rec)


@tool(
    "image_undo",
    "Go back to an earlier version of an image: the one before the current version, "
    "or a specific version number. Nothing is deleted.",
    {
        "type": "object",
        "properties": {
            "image_id": {"type": "string"},
            "to_version": {"type": "integer", "description": "Version to go back to (default: the previous one)."},
        },
        "required": ["image_id"],
    },
)
async def image_undo(args: dict[str, Any]) -> dict[str, Any]:
    try:
        rec = _load(args["image_id"])
        target = args.get("to_version")
        if target is None:
            target = rec.get().parent
            if target is None:
                return _result(f"{rec.id} is already at its original version (v1).", is_error=True)
        image_store.set_current(rec, int(target))
    except (EditError, KeyError, ValueError) as e:
        return _result(f"Undo not done: {e}", is_error=True)
    await _show(rec)
    return _result(f"{rec.id} is back to v{rec.current}. Shown on the canvas.", rec)


@tool(
    "image_versions",
    "List the versions of an image and what each edit did.",
    {"type": "object", "properties": {"image_id": {"type": "string"}}, "required": ["image_id"]},
)
async def image_versions(args: dict[str, Any]) -> dict[str, Any]:
    try:
        rec = _load(args["image_id"])
    except EditError as e:
        return _result(str(e), is_error=True)
    lines = [
        f"v{v.version}{' (current)' if v.version == rec.current else ''}: {v.note}"
        + (f" (from v{v.parent})" if v.parent else "")
        for v in rec.versions
    ]
    return _result(f"{rec.id} '{rec.title}':\n" + "\n".join(lines))
