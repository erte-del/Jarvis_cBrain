"""Textbook: the user's own school textbooks (scanned PDFs on their Mac).

The scans have no text layer, so the first use of a book OCRs every page with tesseract
(a couple of minutes) and keeps the text in storage/textbooks/. The text is only for
finding pages: Claude gets the page images themselves, so it reads the maths exactly as
printed (OCR mangles formulas).
"""

import asyncio
import base64
import io
import os
import re
import subprocess
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pypdf
from claude_agent_sdk import tool

import config

from .syllabus import PAGE, find

DIR = config.STORAGE_DIR / "textbooks"
SCHOOL = Path.home() / "Desktop" / "school"
# book: (title, PDF)
BOOKS = {
    "pure_year1": (
        "Pearson Edexcel AS and A level Mathematics, Pure Mathematics Year 1/AS",
        SCHOOL / "further math\\math" / "Pure math" / "New Edexcel Pure Year 1.pdf",
    ),
}
MAX_PAGES = 4  # images per call
_lock = asyncio.Lock()


def _ocr(page: pypdf.PageObject) -> str:
    buf = io.BytesIO()
    page.images[0].image.convert("L").save(buf, "PNG")
    env = {**os.environ, "OMP_THREAD_LIMIT": "1"}  # one core per page; pages run in parallel
    return subprocess.run(["tesseract", "stdin", "stdout"], input=buf.getvalue(),
                          capture_output=True, env=env, check=True).stdout.decode()


def _index(book: str) -> list[str]:
    path = DIR / f"{book}.txt"
    if not path.exists():
        pdf = pypdf.PdfReader(BOOKS[book][1])
        with ThreadPoolExecutor(os.cpu_count()) as pool:
            text = list(pool.map(_ocr, pdf.pages))
        DIR.mkdir(exist_ok=True)
        path.write_text(PAGE.join(text))
    return path.read_text().split(PAGE)


def _image(book: str, i: int) -> str:
    im = pypdf.PdfReader(BOOKS[book][1]).pages[i].images[0].image.convert("RGB")
    im.thumbnail((1568, 1568))  # Claude's own size limit
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def printed(pages: list[str]) -> list[int]:
    """The printed page number of each PDF page. Scans skip or repeat pages, so each page
    takes the commonest PDF-to-printed offset among its neighbours' page numbers (the last
    line that's just a number; exercise numbers are outvoted)."""
    offs = []
    for i, p in enumerate(pages):
        nums = re.findall(r"^\s*(\d{1,3})\s*$", p, re.M)
        offs.append(i - int(nums[-1]) if nums else None)
    near = lambda i: [o for o in offs[max(0, i - 6):i + 7] if o is not None] or [0]
    return [i - Counter(near(i)).most_common(1)[0][0] for i in range(len(pages))]


def pick(pages: list[str], query: str, page: int | None) -> list[int]:
    """PDF page indexes to show: the printed page asked for (and the next), else the pages
    the query is on, else the contents."""
    if page is not None:
        return [i for i, n in enumerate(printed(pages)) if n in (page, page + 1)][:2]
    if query:
        return find(pages, query)
    return [i for i, p in enumerate(pages[:20]) if p.lstrip().lower().startswith("contents")]


@tool(
    "textbook",
    "The user's own A-level textbooks, as printed pages (images). pure_year1: Pearson "
    "Edexcel Pure Mathematics Year 1/AS (the 9MA0 Pure course). Without query or page: "
    "the contents (chapters, sections, printed page numbers). With query (a topic or the "
    "words on the page, e.g. 'discriminant', 'cosine rule', 'Exercise 3B'): the best "
    "matching pages. With page (a printed page number, e.g. from the contents or 'answers' "
    "at the back): that page and the next. The first call for a book indexes it (a few "
    "minutes).",
    {
        "type": "object",
        "properties": {
            "book": {"type": "string", "enum": list(BOOKS)},
            "query": {"type": "string"},
            "page": {"type": "integer"},
        },
        "required": ["book"],
    },
)
async def textbook(args: dict[str, Any]) -> dict[str, Any]:
    book = args.get("book")
    if book not in BOOKS:
        return {"content": [{"type": "text", "text": f"Unknown book; use one of {list(BOOKS)}."}], "is_error": True}
    title, path = BOOKS[book]
    query = str(args.get("query") or "").strip()
    page = args.get("page")
    try:
        async with _lock:
            pages = await asyncio.to_thread(_index, book)
        hits = pick(pages, query, int(page) if page is not None else None)[:MAX_PAGES]
        numbers = printed(pages)
        images = await asyncio.gather(*(asyncio.to_thread(_image, book, i) for i in hits))
    except (OSError, ValueError, subprocess.CalledProcessError, pypdf.errors.PdfReadError) as e:
        return {"content": [{"type": "text", "text": f"Couldn't read {title} ({path}): {e}"}], "is_error": True}
    if not hits:
        return {"content": [{"type": "text", "text": f"{title}: no page mentions {query or page!r}."}]}
    content: list[dict[str, Any]] = [{"type": "text", "text": f"{title}: printed pages {[numbers[i] for i in hits]}"}]
    for i, data in zip(hits, images):
        content.append({"type": "text", "text": f"[page {numbers[i]}]"})
        content.append({"type": "image", "data": data, "mimeType": "image/jpeg"})
    return {"content": content}
