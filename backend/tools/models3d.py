"""3D objects: fast previews, changes through chat, final file only after approval. (Phase 4d)

Flow (JARVIS_BUILD_PROMPT.md, section 7b):
  preview_3d  -> low-detail preview in the big 3D panel (new version every change)
  revert_3d   -> back to an earlier version
  get_3d_spec -> read back the spec of a version (e.g. after a restart)
  export_3d   -> 'act' tool: goes through the confirmation gate, then Blender builds
                 the detailed final file (.blend, .fbx, .obj, .stl, .gltf, .glb)
"""

import asyncio
import json
import logging
import shutil
import tempfile
import zipfile
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool

import config
import events
import hub
from storage import model_store

from . import shapes

log = logging.getLogger("jarvis.3d")

EXPORT_SCRIPT = Path(__file__).with_name("blender_export_script.py")
BLENDER_TIMEOUT_S = 180

SPEC_DESCRIPTION = (
    "The object as a list of parts. Units are meters, Y is up, sizes realistic. "
    "Each part: {name, shape, position [x,y,z] (the part's center), rotation [x,y,z] degrees, "
    "scale [x,y,z] (optional, e.g. to squash a sphere), color (name or #hex), "
    "material: matte|glossy|metal|glass} plus its shape's fields: "
    "box {size [w,h,d]}; sphere {radius}; cylinder {radius} or {radius_top, radius_bottom}, {height}; "
    "cone {radius, height}; torus {radius, tube} (a ring lying flat); capsule {radius, height (total)}; "
    "lathe {points [[radius, y], ...]} spun around the vertical axis (vases, bottles, lamps); "
    "extrude {outline [[x, y], ...] in the X-Y plane, depth along Z} (signs, flat shapes, profiles). "
    "Round shapes stand upright (axis along Y)."
)


def _text(text: str, is_error: bool = False) -> dict[str, Any]:
    out: dict[str, Any] = {"content": [{"type": "text", "text": text}]}
    if is_error:
        out["is_error"] = True
    return out


async def _show(rec: model_store.ModelRecord) -> None:
    await hub.emit(events.canvas_card(rec.id, "model3d", rec.title, model_store.card_data(rec)))


def _load(model_id: Any) -> model_store.ModelRecord:
    return model_store.load(str(model_id))


# ---- Preview ------------------------------------------------------------------------

def _build_preview(spec: dict[str, Any]) -> tuple[bytes, int, list[float], int]:
    parts = shapes.validate(spec)
    scene = shapes.build_scene(parts, "preview")
    size, triangles = shapes.summary(scene)
    return shapes.to_glb(scene), len(parts), size, triangles


@tool(
    "preview_3d",
    "Make or update a fast, low-detail 3D PREVIEW and show it in the big 3D panel. Use this "
    "whenever the user asks for a 3D object, model, shape or scene. For a change, call it again "
    "with the same model_id and the FULL updated spec; each call is a new version. "
    "This never makes the final file (that's export_3d, only after the user approves). "
    "Use as few parts as show the shape: previews must be fast.",
    {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short name, e.g. 'Wooden chair'."},
            "model_id": {"type": "string", "description": "To update an existing model (e.g. mdl_002)."},
            "note": {"type": "string", "description": "What changed, e.g. 'wider base'."},
            "spec": {
                "type": "object",
                "description": SPEC_DESCRIPTION,
                "properties": {"parts": {"type": "array", "items": {"type": "object"}}},
                "required": ["parts"],
            },
        },
        "required": ["spec"],
    },
)
async def preview_3d(args: dict[str, Any]) -> dict[str, Any]:
    spec = args.get("spec")
    try:
        glb, parts, size, triangles = await asyncio.to_thread(_build_preview, spec)
    except shapes.SpecError as e:
        return _text(f"Preview not made: {e}", is_error=True)
    except Exception as e:  # geometry library errors
        log.exception("3D preview failed")
        return _text(f"Preview not made (geometry error: {e}). Simplify the part that caused it.", is_error=True)

    try:
        rec = _load(args["model_id"]) if args.get("model_id") else model_store.create(str(args.get("title") or "3D object"))
    except KeyError as e:
        return _text(f"Preview not made: {e}", is_error=True)
    if args.get("title"):
        rec.title = str(args["title"])[:80]
    note = str(args.get("note") or ("first version" if not rec.versions else "changed"))
    v = await asyncio.to_thread(model_store.add_version, rec, spec, glb, note, parts, size)
    await _show(rec)
    log.info("3D preview %s v%s: %s parts, %s triangles, size %s", rec.id, v.version, parts, triangles, size)
    w, h, d = size
    return _text(
        f"{rec.id} v{v.version} is showing in the 3D preview panel: {parts} parts, "
        f"{w} × {h} × {d} m (width × height × depth). The user can rotate and zoom it. "
        "Ask what they'd like to change. When they say it's good, ask which file type they want "
        f"({', '.join('.' + f for f in model_store.FORMATS)}) and then call export_3d."
    )


@tool(
    "revert_3d",
    "Go back to an earlier version of a 3D model (default: the previous one). Nothing is deleted.",
    {
        "type": "object",
        "properties": {"model_id": {"type": "string"}, "version": {"type": "integer"}},
        "required": ["model_id"],
    },
)
async def revert_3d(args: dict[str, Any]) -> dict[str, Any]:
    try:
        rec = _load(args["model_id"])
        target = args.get("version") or max(rec.current - 1, 1)
        model_store.set_current(rec, int(target))
    except (KeyError, ValueError) as e:
        return _text(f"Not reverted: {e}", is_error=True)
    await _show(rec)
    return _text(f"{rec.id} is back to v{rec.current} in the preview. Its spec: "
                 + json.dumps(model_store.spec(rec)))


@tool(
    "get_3d_spec",
    "Read back the spec of a 3D model version (default: current), e.g. before changing it "
    "if you no longer have it.",
    {
        "type": "object",
        "properties": {"model_id": {"type": "string"}, "version": {"type": "integer"}},
        "required": ["model_id"],
    },
)
async def get_3d_spec(args: dict[str, Any]) -> dict[str, Any]:
    try:
        rec = _load(args["model_id"])
        v = rec.get(args.get("version"))
    except KeyError as e:
        return _text(str(e), is_error=True)
    return _text(f"{rec.id} '{rec.title}' v{v.version}: " + json.dumps(model_store.spec(rec, v.version)))


# ---- Final export -------------------------------------------------------------------

async def _run_blender(src: Path, dst: Path, fmt: str) -> None:
    blender = config.BLENDER_PATH
    if not Path(blender).exists():
        raise RuntimeError(f"Blender not found at {blender} (set BLENDER_PATH in .env)")
    proc = await asyncio.create_subprocess_exec(
        blender, "--background", "--factory-startup", "--python-exit-code", "1",
        "--python", str(EXPORT_SCRIPT), "--", str(src), str(dst), fmt,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), BLENDER_TIMEOUT_S)
    except TimeoutError:
        proc.kill()
        raise RuntimeError("Blender took too long") from None
    text = out.decode(errors="replace")
    if proc.returncode != 0 or "JARVIS_EXPORT_OK" not in text:
        log.error("Blender export failed:\n%s", text[-3000:])
        raise RuntimeError("Blender couldn't build the file (details in the backend log)")


async def build_final(rec: model_store.ModelRecord, version: int, fmt: str) -> str:
    """Build the detailed model and export it. Returns the stored file name."""
    parts = shapes.validate(model_store.spec(rec, version))
    scene = await asyncio.to_thread(shapes.build_scene, parts, "final")
    glb = await asyncio.to_thread(shapes.to_glb, scene)
    folder = model_store.folder(rec.id)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        src = tmp_dir / "model.glb"
        src.write_bytes(glb)
        out_dir = tmp_dir / "out"
        out_dir.mkdir()
        await _run_blender(src, out_dir / f"model.{fmt}", fmt)
        produced = sorted(out_dir.iterdir())
        if len(produced) == 1:  # a single file (.blend, .fbx, .stl, .glb)
            name = f"final_v{version}.{fmt}"
            shutil.move(produced[0], folder / name)
        else:  # several files (.obj + .mtl, .gltf + .bin): zip them
            name = f"final_v{version}.zip"
            with zipfile.ZipFile(folder / name, "w", zipfile.ZIP_DEFLATED) as z:
                for p in produced:
                    z.write(p, p.name)
    model_store.add_export(rec, version, fmt, name)
    return name


@tool(
    "export_3d",
    "Build the FINAL, detailed 3D file from an approved preview and give it to the user. "
    "Only call this after the user has said the preview is good AND told you the file type. "
    "The user confirms it once more before it runs. Formats: blend, fbx, obj, stl "
    "(millimeters, for 3D printing), gltf, glb.",
    {
        "type": "object",
        "properties": {
            "model_id": {"type": "string"},
            "format": {"type": "string", "enum": model_store.FORMATS},
            "version": {"type": "integer", "description": "Default: the version showing now."},
        },
        "required": ["model_id", "format"],
    },
)
async def export_3d(args: dict[str, Any]) -> dict[str, Any]:
    fmt = str(args.get("format", "")).lower().lstrip(".")
    if fmt not in model_store.FORMATS:
        return _text(f"Unknown format; use one of {model_store.FORMATS}", is_error=True)
    try:
        rec = _load(args["model_id"])
        version = rec.get(args.get("version")).version
    except KeyError as e:
        return _text(str(e), is_error=True)

    log.info("Exporting %s v%s as %s", rec.id, version, fmt)
    try:
        name = await build_final(rec, version, fmt)
    except (RuntimeError, shapes.SpecError) as e:
        return _text(f"Export failed: {e}", is_error=True)
    await _show(rec)
    download = model_store.download_name(rec, name)
    return _text(
        f"Done: {download} is ready. There's a download button in the 3D panel."
        + (" It's a .zip because this format has more than one file." if name.endswith(".zip") else "")
        + (" The STL is in millimeters." if fmt == "stl" else "")
    )
