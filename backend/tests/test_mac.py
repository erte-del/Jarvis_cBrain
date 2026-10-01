"""This Mac: labels, the folder fence, no overwrites, what may be opened, the Python sandbox.
Nothing is opened, copied or changed outside a temp folder.
    .venv/bin/python -m unittest tests.test_mac
"""

import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import config
from tools import mac, maps, registry


def call(handler, **args):
    return asyncio.run(handler.handler(args))


class MacTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name).resolve() / "Jarvis"
        patch = mock.patch.object(config, "FILES_DIR", self.root)
        patch.start()
        self.addCleanup(patch.stop)
        self.calls = []

        async def fake_run(*cmd, **kw):
            self.calls.append(cmd)
            return 0, "", ""

        self.fake_run = fake_run

    def test_labels_and_no_card(self):
        self.assertEqual(registry.classify("mcp__jarvis__mac_read"), "read")
        self.assertEqual(registry.classify("mcp__jarvis__mac_change"), "act")
        self.assertEqual(registry.classify("mcp__jarvis__run_python"), "act")
        self.assertFalse(registry.needs_ok("mcp__jarvis__mac_change", {"action": "trash", "path": "a.txt"}))

    def test_paths_stay_in_the_folder(self):
        self.root.mkdir()
        (self.root.parent / "secret.txt").write_text("x")
        (self.root / "link").symlink_to(self.root.parent)
        for bad in ["../secret.txt", str(self.root.parent / "secret.txt"), "~/.zshrc", "link/secret.txt"]:
            with self.assertRaises(ValueError, msg=bad):
                mac.in_folder(bad)
        self.assertEqual(mac.in_folder(str(self.root / "a.txt")), self.root / "a.txt")

    def test_move_renames_into_folders_and_never_overwrites(self):
        self.root.mkdir()
        (self.root / "a.pdf").write_text("a")
        (self.root / "b.pdf").write_text("b")
        (self.root / "Invoices").mkdir()
        mac.move("a.pdf", "Invoices")
        self.assertTrue((self.root / "Invoices/a.pdf").exists())
        mac.move("Invoices/a.pdf", "2026/March/a.pdf")  # makes the folders
        self.assertTrue((self.root / "2026/March/a.pdf").exists())
        result = call(mac.mac_change, action="move", path="b.pdf", to="2026/March/a.pdf")
        self.assertTrue(result["is_error"])
        self.assertEqual((self.root / "2026/March/a.pdf").read_text(), "a")
        self.assertTrue(call(mac.mac_change, action="move", path="b.pdf", to="../b.pdf")["is_error"])

    def test_only_documents_web_pages_and_real_apps_open(self):
        self.root.mkdir()
        (self.root / "run.command").write_text("echo hi")
        (self.root / "report.pdf").write_text("%PDF")
        with mock.patch.object(mac, "_run", self.fake_run):
            self.assertTrue(call(mac.mac_change, action="open_file", path="run.command")["is_error"])
            self.assertNotIn(("open", str(self.root / "run.command")), self.calls)  # only revealed in Finder
            call(mac.mac_change, action="open_file", path="report.pdf")
            self.assertIn(("open", str(self.root / "report.pdf")), self.calls)
            for url in ["file:///etc/passwd", "whatsapp://send?text=x", "javascript:alert(1)"]:
                self.assertTrue(call(mac.mac_change, action="open_url", url=url)["is_error"], url)
            self.assertTrue(call(mac.mac_change, action="open_app", name=str(self.root / "x.app"))["is_error"])
        self.assertEqual(mac.find_app("finder"), None)  # Finder lives in CoreServices, not Applications
        self.assertEqual(mac.find_app("Calculator"), Path("/System/Applications/Calculator.app"))

    def test_location(self):
        def fake_open(answer):
            async def run(*cmd, **kw):
                self.calls.append(cmd)
                Path(cmd[cmd.index("--stdout") + 1]).write_text(answer)
                return ""
            return run

        with mock.patch.object(mac, "LOCATION_APP", self.root):  # any folder that exists
            for answer, expect in [('{"latitude": 25.1, "longitude": 55.2, "place": "Dubai"}', "Dubai"),
                                   ('{"error": "denied"}', "Location Services")]:
                with mock.patch.object(mac, "_out", fake_open(answer)):
                    self.root.mkdir(exist_ok=True)
                    result = call(mac.mac_read, what="location")
                self.assertIn(expect, result["content"][0]["text"])
                self.assertEqual("is_error" in result, expect != "Dubai")
        with mock.patch.object(mac, "LOCATION_APP", self.root / "missing.app"):
            self.assertIn("setup_location.sh", call(mac.mac_read, what="location")["content"][0]["text"])

    def test_maps(self):
        self.assertEqual(registry.classify("mcp__jarvis__maps"), "read")

        async def fake_run(*cmd, **kw):
            self.calls.append(cmd)
            Path(cmd[cmd.index("--stdout") + 1]).write_text('{"minutes": 20, "to": {"name": "Dubai Mall"}}')
            return 0, "", ""

        with mock.patch.object(mac, "LOCATION_APP", self.root), mock.patch.object(mac, "_run", fake_run):
            self.root.mkdir()
            result = call(maps.maps, action="directions", to="Dubai Mall", arrive_by="2026-10-02T09:00:00+04:00")
            self.assertIn('"minutes": 20', result["content"][0]["text"])
            args = self.calls[-1][self.calls[-1].index("--args") + 1:]
            self.assertEqual(args[0], "directions")
            self.assertEqual(json.loads(args[1]), {"to": "Dubai Mall", "arrive_by": "2026-10-02T09:00:00+04:00"})
            self.assertTrue(call(maps.maps, action="directions")["is_error"])  # no destination
            self.assertTrue(call(maps.maps, action="search", query="x", mode="flying")["is_error"])

    def test_map_card_only_frames_google_maps(self):
        from tools import canvas
        route = canvas.map_data({"from": "25.08,55.25", "to": "25.19,55.27", "mode": "walking", "view": "satellite"})
        self.assertEqual(route["url"], "https://www.google.com/maps?saddr=25.08%2C55.25&daddr=25.19%2C55.27&dirflg=w&t=k&output=embed")
        place = canvas.map_data({"place": "coffee near 25.08,55.25&output=x", "zoom": 14})
        self.assertTrue(place["url"].startswith(canvas.MAP_URL + "q=coffee+near+25.08%2C55.25%26output%3Dx&z=14"))
        with self.assertRaises(ValueError):
            canvas.map_data({})

    @unittest.skipUnless(Path("/usr/bin/sandbox-exec").exists(), "macOS only")
    def test_python_sandbox(self):
        self.root.mkdir()
        (self.root / "data.csv").write_text("a,b\n1,2\n3,4\n")
        outside = self.root.parent / "outside.txt"
        outside.write_text("secret")
        code = f"""
import csv, statistics, subprocess, urllib.request
print("mean", statistics.mean(int(r["b"]) for r in csv.DictReader(open("../data.csv"))))
open("result.txt", "w").write("ok")
for label, f in [("read", lambda: open({str(outside)!r}).read()), ("write", lambda: open("../x.txt", "w")),
                 ("net", lambda: urllib.request.urlopen("https://example.com", timeout=3)),
                 ("exec", lambda: subprocess.run(["/usr/bin/true"]))]:
    try:
        f(); print(label, "ALLOWED")
    except Exception:
        print(label, "blocked")
"""
        text = call(mac.run_python, code=code)["content"][0]["text"]
        self.assertIn("mean 3", text)
        self.assertNotIn("ALLOWED", text)
        self.assertEqual((self.root / "Output/result.txt").read_text(), "ok")
        self.assertFalse((self.root / "x.txt").exists())


if __name__ == "__main__":
    unittest.main()
