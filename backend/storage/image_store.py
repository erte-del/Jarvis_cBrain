"""Images and their versions, stored as files.

    storage/assets/img_001/
        meta.json        title, credit, which version is current, one entry per version
        v1.jpg           the original
        v1_thumb.jpg     small copy for the version strip
        v2.jpg ...       one file per edit; versions are never overwritten

(Phase 6 may move the index into SQLite; the files stay here.)
"""

import io
import json
import re
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from PIL import Image

from config import STORAGE_DIR

ASSETS_DIR = STORAGE_DIR / "assets"
IMAGE_ID = re.compile(r"^img_\d{3,6}$")
THUMB_PX = 256  # version strip
PREVIEW_PX = 512  # the copy Claude looks at
JPEG_QUALITY = 92

_lock = threading.Lock()


@dataclass
class Version:
    version: int
    parent: int | None  # the version this one was made from
    note: str  # "original" or a short description of the edits
    file: str
    width: int
    height: int


@dataclass
class ImageRecord:
    id: str
    title: str
    credit: dict[str, str] = field(default_factory=dict)  # photographer, photographer_url, source_url
    current: int = 1
    versions: list[Version] = field(default_factory=list)

    def get(self, version: int | None = None) -> Version:
        wanted = self.current if version is None else version
        for v in self.versions:
            if v.version == wanted:
                return v
        raise KeyError(f"{self.id} has no version {wanted} (it has v1–v{len(self.versions)})")


def _dir(image_id: str) -> Path:
    if not IMAGE_ID.match(image_id):
        raise KeyError(f"Not an image id: {image_id!r}")
    return ASSETS_DIR / image_id


def _save_meta(rec: ImageRecord) -> None:
    (_dir(rec.id) / "meta.json").write_text(json.dumps(asdict(rec), indent=1))


def load(image_id: str) -> ImageRecord:
    path = _dir(image_id) / "meta.json"
    if not path.exists():
        raise KeyError(f"No image called {image_id}")
    raw = json.loads(path.read_text())
    raw["versions"] = [Version(**v) for v in raw["versions"]]
    return ImageRecord(**raw)


def open_version(rec: ImageRecord, version: int | None = None) -> Image.Image:
    v = rec.get(version)
    img = Image.open(_dir(rec.id) / v.file)
    img.load()
    return img


def _write_version(rec: ImageRecord, img: Image.Image, parent: int | None, note: str) -> Version:
    number = len(rec.versions) + 1
    folder = _dir(rec.id)
    rgb = img.convert("RGB")
    rgb.save(folder / f"v{number}.jpg", "JPEG", quality=JPEG_QUALITY)
    thumb = rgb.copy()
    thumb.thumbnail((THUMB_PX, THUMB_PX))
    thumb.save(folder / f"v{number}_thumb.jpg", "JPEG", quality=85)
    v = Version(number, parent, note, f"v{number}.jpg", rgb.width, rgb.height)
    rec.versions.append(v)
    rec.current = number
    return v


def create(title: str, image_bytes: bytes, credit: dict[str, str]) -> ImageRecord:
    """Store a new image as v1 and return its record."""
    img = Image.open(io.BytesIO(image_bytes))
    img.load()
    with _lock:
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        numbers = [int(p.name[4:]) for p in ASSETS_DIR.glob("img_*") if IMAGE_ID.match(p.name)]
        image_id = f"img_{max(numbers, default=0) + 1:03d}"
        _dir(image_id).mkdir()
        rec = ImageRecord(id=image_id, title=title, credit=credit)
        _write_version(rec, img, None, "original")
        _save_meta(rec)
    return rec


def add_version(rec: ImageRecord, img: Image.Image, parent: int, note: str) -> Version:
    with _lock:
        v = _write_version(rec, img, parent, note)
        _save_meta(rec)
    return v


def set_current(rec: ImageRecord, version: int) -> None:
    rec.get(version)  # raises if it doesn't exist
    rec.current = version
    _save_meta(rec)


def preview_jpeg(rec: ImageRecord, version: int | None = None) -> bytes:
    """A small JPEG of a version, for Claude to look at."""
    img = open_version(rec, version).convert("RGB")
    img.thumbnail((PREVIEW_PX, PREVIEW_PX))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=80)
    return buf.getvalue()


def file_path(image_id: str, filename: str) -> Path:
    """Path of a stored file, for the web server. Only v<n>.jpg / v<n>_thumb.jpg."""
    if not re.fullmatch(r"v\d{1,4}(_thumb)?\.jpg", filename):
        raise KeyError(filename)
    path = _dir(image_id) / filename
    if not path.exists():
        raise KeyError(filename)
    return path


def card_data(rec: ImageRecord) -> dict[str, Any]:
    """What the canvas needs to show this image and its version strip."""
    base = f"/assets/{rec.id}"
    return {
        "image_id": rec.id,
        "current": rec.current,
        "credit": rec.credit,
        "versions": [
            {
                "version": v.version,
                "note": v.note,
                "url": f"{base}/{v.file}",
                "thumb_url": f"{base}/v{v.version}_thumb.jpg",
                "width": v.width,
                "height": v.height,
            }
            for v in rec.versions
        ],
    }
