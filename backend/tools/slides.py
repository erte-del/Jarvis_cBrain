"""Slides: PowerPoint lessons in the style of the user's computing teacher.

The template is the teacher's own deck (PG Online's AQA design) with its slides taken out,
kept in storage/slides/template.pptx (not in git: it's PG Online's). Each deck is built
from its layouts: title, hook question, objectives, teaching slides, activities, end.
Decks are saved in the Output folder of Jarvis's files and opened.
"""

import asyncio
import base64
import copy
import io
import math
import subprocess
from pathlib import Path
from typing import Any

from claude_agent_sdk import tool
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.text import PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Pt

import config
from storage import image_store

TEMPLATE = config.STORAGE_DIR / "slides" / "template.pptx"
LECTURES = Path.home() / "Desktop" / "school" / "computing" / "class lectures"
RENDERS = config.STORAGE_DIR / "lectures"
CHECKS = config.STORAGE_DIR / "slides" / "checks"  # pictures of Jarvis's own decks, to look over
SHEET = 9  # slides per contact sheet
MAX_SEEN = 6  # slide pictures per call
COURSE = ["AQA", "AS Level", "Computer Science", "Paper 2"]
# slide kind: the teacher's layout for it
LAYOUTS = {"hook": "4_Custom Layout", "objectives": "7_Custom Layout", "content": "3_Custom Layout",
           "practice": "2_Custom Layout"}
LINE = Emu(420_000)  # height of one line of 24pt body text
CHARS = 52  # characters in one line of 24pt body text across the full width
GAP = Emu(150_000)
ROW = Emu(324_000)  # the teacher's table rows and narrowest columns
COLUMN = Emu(468_000)
BOTTOM = Emu(6_200_000)  # above the PG Online logo
ACCENT = RGBColor(0xA4, 0x1E, 0x21)  # the template's red, where the teacher uses their unit's colour
REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"
_keynote = asyncio.Lock()


def _fill(frame, points: list[str], white: bool = True) -> None:
    """Bullets; '- ' makes a sub-point, a line ending in ':' is a bold heading and **key terms**
    are coloured, as the teacher does (bold on a coloured slide, where the colour would vanish)."""
    frame.text = ""
    for i, point in enumerate(points):
        para = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        sub = point.startswith("- ")
        para.level = 1 if sub else 0
        for j, part in enumerate((point[2:] if sub else point).split("**")):
            if not part:
                continue
            run = para.add_run()
            run.text = part
            run.font.bold = point.rstrip().endswith(":") or (j % 2 and not white) or None
            if j % 2 and white:
                run.font.color.rgb = ACCENT
            elif sub:  # the layout greys sub-points out; the teacher makes them black
                run.font.color.theme_color = MSO_THEME_COLOR.TEXT_1
        if sub:
            para.space_after = Pt(12)


def _table(slide, rows: list[list[str]], left: int, top: int, room: int) -> None:
    """A compact table like the teacher's: columns as wide as their text, centred, coloured header."""
    cols = max(len(r) for r in rows)
    widths = [max(COLUMN, Emu(110_000 * max(len(str(r[c])) if c < len(r) else 0 for r in rows) + 200_000))
              for c in range(cols)]
    shrink = min(1, room / sum(widths))
    table = slide.shapes.add_table(len(rows), cols, left, top, int(sum(widths) * shrink), ROW * len(rows)).table
    table.horz_banding = False
    for c, w in enumerate(widths):
        table.columns[c].width = Emu(int(w * shrink))
    for r, row in enumerate(rows):
        table.rows[r].height = ROW
        for c in range(cols):
            cell = table.cell(r, c)
            cell.text = str(row[c]) if c < len(row) else ""
            cell.fill.solid()
            cell.fill.fore_color.rgb = ACCENT if r == 0 else RGBColor(0xF2, 0xF2, 0xF2)
            for para in cell.text_frame.paragraphs:
                para.alignment = PP_ALIGN.CENTER
                for run in para.runs:
                    run.font.size = Pt(16)


def _picture(slide, image_id: str, left: int, top: int, width: int, height: int) -> None:
    """A picture from Jarvis's images (image_search, generate_image), as big as fits the box."""
    rec = image_store.load(image_id)
    path = image_store.file_path(image_id, rec.get().file)
    with Image.open(path) as img:
        w, h = img.size
    scale = min(width / w, height / h)
    pw, ph = int(w * scale), int(h * scale)
    slide.shapes.add_picture(str(path), left + (width - pw) // 2, top, pw, ph)


def _text_height(points: list[str], width: int, full: int, size: int = 24) -> int:
    """About how tall the points come out, wrapped to the box's width."""
    per = CHARS * width / full * 24 / size
    return int(sum(max(1, math.ceil(len(p.replace("**", "")) / per)) for p in points) * LINE * size / 24)


def _figure(src, dst, below: int) -> int:
    """The teacher's diagrams, pictures, labels and tables from one of their slides. Both decks
    are on the same template, so they land where the teacher put them, moved down (as far as
    the slide allows) to start below `below`. Returns where the figure starts."""
    shapes = [sh for sh in src.shapes if not sh.is_placeholder and sh.top is not None]
    if not shapes:
        return BOTTOM
    top = min(sh.top for sh in shapes)
    shift = max(0, min(below - top, BOTTOM - max(sh.top + sh.height for sh in shapes)))
    tree = dst.shapes._spTree
    for shape in shapes:
        el = copy.deepcopy(shape._element)
        for blip in el.iter(qn("a:blip")):
            blob = src.part.related_part(blip.get(qn("r:embed"))).blob
            blip.set(qn("r:embed"), dst.part.get_or_add_image_part(io.BytesIO(blob))[1])
        if any(k.startswith(REL) for e in el.iter() for k in e.attrib
               if not (e.tag == qn("a:blip") and k == qn("r:embed"))):
            continue  # links, sound or video: would point at nothing here
        tree.insert_element_before(el, "p:extLst")
        for pr in el.iter(qn("p:cNvPr")):  # ids must stay unique on the slide
            pr.set("id", str(dst.shapes._next_shape_id))
        dst.shapes[-1].top += shift
    return top + shift


def _deck(name: str) -> Path | None:
    """The teacher's deck whose file name contains name."""
    want = name.strip().lower()
    return next((d for d in sorted(LECTURES.glob("*.pptx")) if want in d.stem.lower()), None) if want else None


def _set(shape, lines: list[str]) -> None:
    """Replace a template text box's lines, keeping each line's formatting."""
    paras = shape.text_frame.paragraphs
    for para, line in zip(paras, lines):
        for run in para.runs[1:]:
            run._r.getparent().remove(run._r)
        if para.runs:
            para.runs[0].text = line
        else:
            para.add_run().text = line


def build(args: dict[str, Any], path: Path) -> tuple[int, list[str]]:
    deck = Presentation(str(TEMPLATE))
    title, unit, topic = args["title"], str(args.get("unit") or ""), str(args.get("topic") or "").strip()
    topic = topic if topic.isdigit() else ""  # it goes in the little hexagon
    teacher: dict[Path, Any] = {}
    warnings = []
    # The layouts carry the topic: the number in the hexagon and the footer on every slide.
    for layout in deck.slide_layouts:
        for shape in layout.shapes:
            if shape.is_placeholder or not shape.has_text_frame or not shape.text_frame.text.strip():
                continue
            if shape.name.startswith("Hexagon"):
                _set(shape, [topic])
            else:
                _set(shape, [unit, f"Topic {topic} {title}" if topic else title])

    first = deck.slides.add_slide(deck.slide_layouts.get_by_name("Title Slide"))
    box = first.placeholders[10]
    box.left, box.top, box.width, box.height = box.left, box.top, Emu(2_750_617), box.height  # as wide as the teacher's
    box.text_frame.text = ""
    for i, line in enumerate(args.get("course") or COURSE):
        para = box.text_frame.paragraphs[0] if i == 0 else box.text_frame.add_paragraph()
        para.level = [0, 2, 3, 3][min(i, 3)]  # the layout's styles: AQA, AS Level, subject, paper
        run = para.add_run()
        run.text = line
        if i > 1:
            run.font.size = Pt(24)
    _fill(first.placeholders[11].text_frame, [title, "", unit])

    for number, s in enumerate(args.get("slides") or [], 2):
        kind = s.get("kind", "content")
        slide = deck.slides.add_slide(deck.slide_layouts.get_by_name(LAYOUTS.get(kind, LAYOUTS["content"])))
        points = [str(p) for p in s.get("points") or []]
        slide.placeholders[13].text = s.get("title") or ("Objectives" if kind == "objectives" else "")
        _fill(slide.placeholders[14].text_frame, points, kind not in ("hook", "objectives"))
        body = slide.placeholders[14]
        rows, picture = s.get("table") or [], str(s.get("picture") or "")
        # A placeholder inherits its box; set all of it, or the width becomes 0.
        left, top, width, height = body.left, body.top, body.width, body.height
        if picture and points:  # text on the left, the picture on the right
            width = int(body.width * 0.55)
            _picture(slide, picture, left + int(body.width * 0.58), top, int(body.width * 0.42), BOTTOM - top)
        elif picture:
            _picture(slide, picture, left, top, body.width, BOTTOM - top)
        if rows:
            height = max(_text_height(points, width, body.width), LINE)
            _table(slide, rows, left, top + height + GAP, width)
        if s.get("figure"):
            fig = s["figure"]
            src = _deck(str(fig.get("deck") or ""))
            if src is None:
                raise ValueError(f"no teacher's deck called {fig.get('deck')!r}")
            teacher.setdefault(src, Presentation(str(src)))
            n = int(fig.get("slide") or 0)
            if not 1 <= n <= len(teacher[src].slides):
                raise ValueError(f"{src.stem} has no slide {n}")
            # The teacher's figure sat under their own short text; ours may be longer.
            room = _figure(teacher[src].slides[n - 1], slide, top + _text_height(points, width, body.width) + GAP) - GAP - top
            height = max(room, 0)
            fits = lambda pts: next((z for z in range(24, 15, -1) if _text_height(pts, width, body.width, z) <= room), 0)
            kept = list(points)
            while kept and not fits(kept):  # the last points go to the notes until the rest fit
                kept.pop()
            if len(kept) < len(points):
                moved = "\n".join(p.replace("**", "") for p in points[len(kept):])
                s["notes"] = moved + ("\n\n" + s["notes"] if s.get("notes") else "")
                _fill(slide.placeholders[14].text_frame, kept)
                warnings.append(f"slide {number}: {len(points) - len(kept)} of its points didn't fit above "
                                "the figure and went into the notes")
            size = fits(kept) if kept else 24
            if size < 24:
                for para in slide.placeholders[14].text_frame.paragraphs:
                    for run in para.runs:
                        run.font.size = Pt(size)
                if size < 20:
                    warnings.append(f"slide {number}: the points were shrunk to {size}pt to fit above the figure")
        body.left, body.top, body.width, body.height = left, top, width, height
        if s.get("notes"):
            slide.notes_slide.notes_text_frame.text = s["notes"]

    deck.slides.add_slide(deck.slide_layouts.get_by_name("8_Custom Layout"))
    deck.save(str(path))
    return len(deck.slides), warnings


def _free(name: str) -> Path:
    out = config.FILES_DIR / "Output"
    out.mkdir(parents=True, exist_ok=True)
    stem = "".join(c for c in name if c not in '/\\:*?"<>|').strip() or "Slides"
    path, n = out / f"{stem}.pptx", 2
    while path.exists():
        path, n = out / f"{stem} {n}.pptx", n + 1
    return path


@tool(
    "make_slides",
    "Make a PowerPoint (.pptx) lesson in the user's computing teacher's design (AQA, PG Online "
    "template) and save it in Jarvis's Output folder. It isn't opened: you get every slide back as "
    "a picture to check, then fix it (again with replace) or hand it over with open_slides. Give "
    "the whole deck at once. The "
    "title slide and the end slide are added for you. Each slide: kind (hook: an opening question "
    "in points; objectives: 'Knowledge:' and 'Skills:' headings with '- ' points under them; "
    "content: a teaching slide; practice: questions for the user to solve), title, points (short bullets; "
    "'- ' starts a sub-point, a line ending in ':' is a bold heading, **key term** is coloured), "
    "optional table (rows of cells, first row the header), optional picture (an image id from "
    "image_search or generate_image, put on the right of the points, or filling the slide without "
    "points), optional figure ({deck, slide}: copies the diagrams, labels and tables of a slide of "
    "the teacher's, where lectures shows [diagram] or [picture], into the same place; write no more "
    "text than the teacher's slide has, since it is moved down or shrunk to clear your points and "
    "points that still don't fit go to the notes; give no table), optional notes (speaker notes).",
    {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "the lesson, e.g. 'Binary arithmetic'"},
            "unit": {"type": "string", "description": "the spec section, e.g. 'Data representation'"},
            "topic": {"type": "string", "description": "the topic number in the unit, e.g. '3' (a number only)"},
            "replace": {"type": "string", "description": "a deck this tool made, to overwrite with the fixed one"},
            "course": {"type": "array", "items": {"type": "string"},
                       "description": f"title slide lines; default {COURSE}"},
            "slides": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "kind": {"type": "string", "enum": list(LAYOUTS)},
                        "title": {"type": "string"},
                        "points": {"type": "array", "items": {"type": "string"}},
                        "table": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}},
                        "picture": {"type": "string", "description": "image id, e.g. img_004"},
                        "figure": {"type": "object", "properties": {
                            "deck": {"type": "string"}, "slide": {"type": "integer"}}},
                        "notes": {"type": "string"},
                    },
                },
            },
        },
        "required": ["title", "slides"],
    },
)
async def make_slides(args: dict[str, Any]) -> dict[str, Any]:
    if not TEMPLATE.exists():
        return {"content": [{"type": "text", "text": f"The slide template is missing: {TEMPLATE}"}], "is_error": True}
    again = Path(str(args.get("replace") or "")).expanduser()
    out = config.FILES_DIR / "Output"
    path = again if again.suffix == ".pptx" and again.parent == out and again.exists() else _free(str(args.get("title") or ""))
    try:
        count, warnings = await asyncio.to_thread(build, args, path)
    except (KeyError, ValueError, TypeError, OSError) as e:
        return {"content": [{"type": "text", "text": f"Couldn't build the deck: {e!r}"}], "is_error": True}
    text = f"Saved {path} ({count} slides). Not opened yet: check it first."
    if warnings:
        text += " Crowded: " + "; ".join(warnings) + "."
    try:
        async with _keynote:
            pictures = await asyncio.to_thread(render, path, CHECKS / path.stem)
    except (OSError, subprocess.SubprocessError) as e:
        text += f" Couldn't draw the slides to check them ({e!r}); call open_slides to hand it over."
        return {"content": [{"type": "text", "text": text}]}
    text += (" Here is every slide as Keynote draws it, numbered. Look over each one for text "
             "running into a figure, table or picture, text cut off, off the slide or tiny, "
             "overlapping shapes, empty or wrong slides. If any slide is wrong, fix it and call "
             f"make_slides again with the whole deck and replace: {str(path)!r}. When every slide "
             f"is right, call open_slides with {str(path)!r}.")
    content: list[dict[str, Any]] = [{"type": "text", "text": text}]
    for sheet in await asyncio.to_thread(_sheets, pictures):
        content.append({"type": "image", "data": base64.b64encode(sheet).decode(), "mimeType": "image/jpeg"})
    return {"content": content}


def _sheets(pictures: list[Path], width: int = 600) -> list[bytes]:
    """The slide pictures, numbered, nine to a JPEG, so a deck is a few pictures to look over."""
    font = ImageFont.load_default(size=28)
    out = []
    for first in range(0, len(pictures), SHEET):
        batch = pictures[first:first + SHEET]
        with Image.open(batch[0]) as im:
            height = width * im.height // im.width
        sheet = Image.new("RGB", (3 * width, (len(batch) + 2) // 3 * height), "white")
        for i, picture in enumerate(batch):
            with Image.open(picture) as im:
                cell = im.convert("RGB").resize((width, height))
            draw = ImageDraw.Draw(cell)
            draw.rectangle((0, 0, width - 1, height - 1), outline="grey")
            draw.text((8, 4), str(first + i + 1), fill="red", font=font)
            sheet.paste(cell, (i % 3 * width, i // 3 * height))
        buf = io.BytesIO()
        sheet.save(buf, "JPEG", quality=80)
        out.append(buf.getvalue())
    return out


@tool(
    "open_slides",
    "Open a deck make_slides made, to hand it to the user, once you've checked every slide.",
    {"type": "object", "properties": {"file": {"type": "string"}}, "required": ["file"]},
)
async def open_slides(args: dict[str, Any]) -> dict[str, Any]:
    path = Path(str(args.get("file") or "")).expanduser()
    if path.suffix != ".pptx" or path.parent != config.FILES_DIR / "Output" or not path.exists():
        return {"content": [{"type": "text", "text": f"No deck at {path}"}], "is_error": True}
    subprocess.run(["open", str(path)], check=False)
    return {"content": [{"type": "text", "text": f"Opened {path}."}]}


def read_deck(path: Path) -> list[str]:
    """Each slide's text: titles and bullets, tables as rows, then speaker notes."""
    out = []
    for n, slide in enumerate(Presentation(str(path)).slides, 1):
        hidden = " hidden" if slide._element.get("show") == "0" else ""
        lines = [f"--- Slide {n} ({slide.slide_layout.name}{hidden})"]
        for shape in slide.shapes:
            if shape.has_text_frame and shape.text_frame.text.strip():
                lines += ["  " * p.level + p.text for p in shape.text_frame.paragraphs if p.text.strip()]
            elif shape.has_table:
                lines += [" | ".join(c.text for c in row.cells) for row in shape.table.rows]
            elif shape.shape_type == 13:  # picture
                lines.append("[picture]")
        if any(not sh.is_placeholder and sh.shape_type not in (13, 17) and not sh.has_table for sh in slide.shapes):
            lines.append("[diagram]")  # drawn shapes: gate symbols, circuits, arrows
        if slide.has_notes_slide and slide.notes_slide.notes_text_frame.text.strip():
            lines.append("Notes: " + slide.notes_slide.notes_text_frame.text.strip())
        out.append("\n".join(lines))
    return out


EXPORT = """on run argv
  tell application "Keynote"
    repeat 60 times
      if exists document (item 1 of argv) then exit repeat
      delay 1
    end repeat
    set d to document (item 1 of argv)
    export d to POSIX file (item 2 of argv) as slide images with properties ¬
      {image format:JPEG, compression factor:0.8}
    close d saving no
  end tell
end run"""


def render(path: Path, out: Path | None = None) -> list[Path]:
    """Every shown slide as a picture (Keynote leaves hidden ones out), drawn by Keynote once
    and kept in storage/lectures/ (or out), and drawn again when the deck changes.
    Keynote opens the deck by itself (AppleScript's own open can't read the Desktop)."""
    out = out or RENDERS / path.stem
    if not out.exists() or out.stat().st_mtime < path.stat().st_mtime:
        out.mkdir(parents=True, exist_ok=True)
        for old in out.glob("*.jpeg"):
            old.unlink()
        subprocess.run(["open", "-g", "-a", "Keynote", str(path)], check=True)
        subprocess.run(["osascript", "-", path.stem, str(out)], input=EXPORT.encode(),
                       capture_output=True, check=True, timeout=180)
        out.touch()
    return sorted(out.glob("*.jpeg"))


@tool(
    "lectures",
    "The user's computing teacher's own lesson decks (AQA Computer Science, PowerPoint). Without "
    "deck: the list. With deck (part of a file name, e.g. 'Topic 3' or 'sound'): the text of every "
    "slide, with its layout, tables and speaker notes. With slides too (slide numbers, up to "
    f"{MAX_SEEN}): those slides as pictures, to see their diagrams, images and layout; the first "
    "time for a deck takes a minute. [diagram] and [picture] mark slides make_slides can copy figures "
    "from. Read one before make_slides as the example to follow.",
    {
        "type": "object",
        "properties": {
            "deck": {"type": "string"},
            "slides": {"type": "array", "items": {"type": "integer"}},
        },
    },
)
async def lectures(args: dict[str, Any]) -> dict[str, Any]:
    deck = _deck(str(args.get("deck") or ""))
    if deck is None:
        names = "\n".join(d.stem for d in sorted(LECTURES.glob("*.pptx"))) or f"none in {LECTURES}"
        return {"content": [{"type": "text", "text": f"The teacher's decks:\n{names}"}]}
    seen = [int(n) for n in args.get("slides") or []][:MAX_SEEN]
    try:
        texts = await asyncio.to_thread(read_deck, deck)
        if not seen:
            return {"content": [{"type": "text", "text": deck.stem + "\n" + "\n".join(texts)}]}
        seen = [n for n in seen if 1 <= n <= len(texts)]
        async with _keynote:
            pictures = await asyncio.to_thread(render, deck)
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as e:
        return {"content": [{"type": "text", "text": f"Couldn't read {deck.name}: {e!r}"}], "is_error": True}
    content: list[dict[str, Any]] = [{"type": "text", "text": deck.stem}]
    shown = [n for n, text in enumerate(texts, 1) if " hidden)" not in text.split("\n")[0]]
    for n in seen:
        content.append({"type": "text", "text": texts[n - 1]})
        if n in shown and shown.index(n) < len(pictures):
            data = base64.b64encode(pictures[shown.index(n)].read_bytes()).decode()
            content.append({"type": "image", "data": data, "mimeType": "image/jpeg"})
    return {"content": content}
