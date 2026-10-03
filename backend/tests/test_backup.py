"""scripts/backup.sh: a backup made in one project folder restores into another.
Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "backup.sh"
CHAT_ID = "fb829e7e-0638-4ac3-bd1e-b670ea7ea063"


def project(home: Path, name: str) -> Path:
    root = home / name
    (root / "scripts").mkdir(parents=True)
    (root / "backend/storage").mkdir(parents=True)
    shutil.copy(SCRIPT, root / "scripts")
    return root


def sessions(home: Path, root: Path) -> Path:
    # .resolve(): the script sees the real path (on macOS /var is /private/var).
    return home / ".claude/projects" / re.sub(r"[^a-zA-Z0-9]", "-", str((root / "backend/storage").resolve()))


def run(home: Path, root: Path, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
    return subprocess.run([root / "scripts/backup.sh", *args], env={"HOME": str(home), "PATH": "/usr/bin:/bin"},
                          input=stdin, capture_output=True, text=True)


class BackupTest(unittest.TestCase):
    def test_backup_restores_into_another_folder(self):
        home = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, home)
        old, new = project(home, "old"), project(home, "new_mac")
        (old / ".env").write_text("PEXELS_API_KEY=abc\n")
        (old / "backend/storage/memory.json").write_text("[1]")
        (old / "backend/storage/chats.json").write_text(f'{{"{CHAT_ID}": {{}}}}')
        (old / "backend/storage/assets/img_001").mkdir(parents=True)
        (old / "backend/storage/assets/img_001/v1.jpg").write_bytes(b"jpg")
        (old / "backend/storage/ultron.log").write_text("noise")
        sessions(home, old).mkdir(parents=True)
        (sessions(home, old) / f"{CHAT_ID}.jsonl").write_text("saved chat")
        (sessions(home, old) / "11111111-1111-1111-1111-111111111111.jsonl").write_text("not saved")

        res = run(home, old)
        self.assertEqual(res.returncode, 0, res.stderr)
        backup = next(home.glob("Ultron-backup-*.tgz"))
        self.assertEqual(backup.stat().st_mode & 0o077, 0)  # it holds keys: only you can read it

        self.assertEqual(run(home, new, "restore", str(backup)).returncode, 0)
        self.assertEqual((new / ".env").read_text(), "PEXELS_API_KEY=abc\n")
        self.assertEqual((new / "backend/storage/memory.json").read_text(), "[1]")
        self.assertEqual((new / "backend/storage/assets/img_001/v1.jpg").read_bytes(), b"jpg")
        self.assertFalse((new / "backend/storage/ultron.log").exists())
        self.assertFalse((new / "sessions").exists())
        self.assertEqual([p.name for p in sessions(home, new).iterdir()], [f"{CHAT_ID}.jsonl"])

        # Restoring over existing data asks first.
        (new / ".env").write_text("changed")
        self.assertNotEqual(run(home, new, "restore", str(backup), stdin="no\n").returncode, 0)
        self.assertEqual((new / ".env").read_text(), "changed")
        self.assertEqual(run(home, new, "restore", str(backup), stdin="yes\n").returncode, 0)
        self.assertEqual((new / ".env").read_text(), "PEXELS_API_KEY=abc\n")


if __name__ == "__main__":
    unittest.main()
