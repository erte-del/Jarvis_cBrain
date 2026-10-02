"""Syllabus: what the user's A-level exam boards say is on each course.

The official specification PDFs are public, so the first lookup for a subject downloads
its PDF and keeps the text in storage/syllabus/ (not in git: the text is the exam
board's). Pages are matched by the words asked about; Claude reads the page text, and
explains the topic in the spec's terms. The links say where to practise.
"""

import asyncio
import io
import re
import urllib.request
from typing import Any

import pypdf
from claude_agent_sdk import tool

import config

DIR = config.STORAGE_DIR / "syllabus"
MAX_CHARS = 12_000
PEARSON = "https://qualifications.pearson.com/content/dam/pdf/A%20Level/Mathematics/2017/specification-and-sample-assesment/"
PMT = "https://www.physicsandmathstutor.com/"
# subject: (name, spec PDF, where to practise)
SPECS = {
    "computer_science": (
        "AQA A-level Computer Science (7517)",
        "https://filestore.aqa.org.uk/resources/computing/specifications/AQA-7516-7517-SP-2015.PDF",
        f"notes and questions: https://adacomputerscience.org, {PMT}computer-science-revision/a-level-aqa/",
    ),
    "maths": (
        "Pearson Edexcel A level Mathematics (9MA0): Pure, Statistics, Mechanics",
        PEARSON + "a-level-l3-mathematics-specification-issue4.pdf",
        f"notes: {PMT}maths-revision/a-level-edexcel/, past papers by topic: {PMT}a-level-maths-papers/edexcel/",
    ),
    "further_maths": (
        "Pearson Edexcel A level Further Mathematics (9FM0): Core Pure and all options "
        "(Further Pure 1-2, Further Statistics 1-2, Further Mechanics 1-2, Decision 1-2)",
        PEARSON + "a-level-l3-further-mathematics-specification.pdf",
        f"past papers by topic: {PMT}a-level-maths-papers/edexcel-further/",
    ),
}
PAGE = "\n\f"  # between pages in the saved text
_lock = asyncio.Lock()


def _download(subject: str) -> list[str]:
    path = DIR / f"{subject}.txt"
    if not path.exists():
        req = urllib.request.Request(SPECS[subject][1], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            pdf = pypdf.PdfReader(io.BytesIO(r.read()))
        DIR.mkdir(exist_ok=True)
        path.write_text(PAGE.join(p.extract_text() or "" for p in pdf.pages))
    return path.read_text().split(PAGE)


def find(pages: list[str], query: str) -> list[int]:
    """Indexes of the pages to show: the course overview without a query, else the three
    pages with the most hits for the query's words (most first)."""
    if not query:
        at = [i for i, p in enumerate(pages) if "content overview" in p.lower() or "at a glance" in p.lower()]
        return sorted({j for i in at for j in (i, i + 1) if j < len(pages)})
    words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2] or [query.lower()]
    score = {i: sum(p.lower().count(w) for w in words) for i, p in enumerate(pages)}
    # Pages with every word first, then by hits.
    best = sorted(score, key=lambda i: (all(w in pages[i].lower() for w in words), score[i]), reverse=True)
    return [i for i in best[:3] if score[i]]


@tool(
    "syllabus",
    "The official exam specification of the user's A-level courses: AQA Computer Science "
    "(7517), Edexcel Maths (9MA0: Pure, Statistics, Mechanics) and Edexcel Further Maths "
    "(9FM0, every option: the user hasn't picked theirs). Without query: the course "
    "overview (papers and topics). With query (a topic, e.g. 'hash tables', 'binomial "
    "distribution', 'moments'): the spec pages about it, with page numbers, exactly what "
    "students must know. Also returns where to practise. The first call for a subject "
    "downloads its spec (a few seconds).",
    {
        "type": "object",
        "properties": {
            "subject": {"type": "string", "enum": list(SPECS)},
            "query": {"type": "string"},
        },
        "required": ["subject"],
    },
)
async def syllabus(args: dict[str, Any]) -> dict[str, Any]:
    subject = args.get("subject")
    if subject not in SPECS:
        return {"content": [{"type": "text", "text": f"Unknown subject; use one of {list(SPECS)}."}], "is_error": True}
    query = str(args.get("query") or "").strip()
    name, url, practise = SPECS[subject]
    try:
        async with _lock:
            pages = await asyncio.to_thread(_download, subject)
    except (OSError, ValueError, pypdf.errors.PdfReadError) as e:
        return {"content": [{"type": "text", "text": f"Couldn't get the {name} spec: {e}"}], "is_error": True}
    hits = find(pages, query)
    if not hits:
        body = f"Nothing in the spec mentions {query!r}: it's probably not on this course."
    else:
        body = "\n\n".join(f"[spec page {i + 1}]\n{pages[i].strip()}" for i in hits)[:MAX_CHARS]
    return {"content": [{"type": "text", "text": f"{name}\nSpec: {url}\nPractise: {practise}\n\n{body}"}]}
