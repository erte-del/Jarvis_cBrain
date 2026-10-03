"""Read/act labels. Run from the backend folder:
    .venv/bin/python -m unittest discover tests

If a tool is labelled 'read' it runs without asking you, so these tests matter.
"""

import tempfile
import unittest
from pathlib import Path

from tools import registry


class ClassifyTest(unittest.TestCase):
    def assert_kind(self, kind: str, names: list[str]) -> None:
        for name in names:
            self.assertEqual(registry.classify(name), kind, name)

    def test_connector_reads_run_freely(self):
        self.assert_kind("read", [
            "mcp__claude_ai_Gmail__search_threads",
            "mcp__claude_ai_Gmail__get_thread",
            "mcp__claude_ai_Gmail__list_labels",
            "mcp__claude_ai_Canva__search-designs",
            "mcp__claude_ai_Resend__list-emails",
            "mcp__claude_ai_Supabase__query_logs",
            "mcp__claude_ai_Claude_Docs__query",
        ])

    def test_connector_actions_ask(self):
        self.assert_kind("act", [
            "mcp__claude_ai_Gmail__send_message",
            "mcp__claude_ai_Gmail__reply",
            "mcp__claude_ai_Gmail__forward",
            "mcp__claude_ai_Gmail__create_draft",
            "mcp__claude_ai_Gmail__trash_thread",
            "mcp__claude_ai_Gmail__update_message_labels",
            "mcp__claude_ai_Gmail__mark_thread_spam",
            "mcp__claude_ai_Supabase__execute_sql",
            "mcp__claude_ai_Supabase__delete_branch",
            "mcp__claude_ai_Resend__send-email",
            "mcp__claude_ai_Canva__export-design",
            "mcp__claude_ai_Replit__publish_app",
            "mcp__claude_ai_Gmail__getaway",  # 'getaway' is not 'get'
            "mcp__claude_ai_Gmail__",  # malformed
        ])

    def test_unknown_tools_ask(self):
        self.assert_kind("act", ["Bash", "Write", "mcp__some_local_server__get_secrets", "mcp__ultron__unknown"])

    def test_builtins_and_own_tools(self):
        self.assert_kind("read", ["WebSearch", "WebFetch", "ToolSearch",
                                  "mcp__ultron__ask_expert", "mcp__ultron__show_on_canvas"])

    def test_friendly_names(self):
        self.assertEqual(registry.friendly_name("mcp__claude_ai_Gmail__send_message"), "Gmail: Send message")
        self.assertEqual(registry.friendly_name("mcp__claude_ai_Claude_Docs__query"), "Claude Docs: Query")
        self.assertEqual(registry.friendly_name("mcp__claude_ai_Canva__search-designs"), "Canva: Search designs")
        self.assertEqual(registry.friendly_name("mcp__ultron__show_on_canvas"), "Show on canvas")

    def test_confirmation_details_are_readable(self):
        title, _, details = registry.describe_call(
            "mcp__claude_ai_Gmail__create_draft", {"to": ["a@b.com", "c@d.com"], "subject": "Hi"}
        )
        self.assertEqual(title, "Gmail: Create draft")
        self.assertEqual(details, [["to", "a@b.com, c@d.com"], ["subject", "Hi"]])


class NeedsOkTest(unittest.TestCase):
    """In chat, only what reaches other people or important files shows a card."""

    def setUp(self):
        self._file = registry.important.IMPORTANT_FILE
        registry.important.IMPORTANT_FILE = Path(tempfile.mkdtemp()) / "important.json"

    def tearDown(self):
        registry.important.IMPORTANT_FILE = self._file

    def test_simple_actions_just_run(self):
        for name, args in [
            ("mcp__claude_ai_TickTick__create_task", {"task": {"title": "Timer"}}),
            ("mcp__claude_ai_TickTick__delete_task", {"task_id": "t1"}),
            ("mcp__claude_ai_Google_Calendar__create_event", {"summary": "Study", "attendees": []}),
            ("mcp__claude_ai_Gmail__create_draft", {"to": ["a@b.com"]}),
            ("mcp__claude_ai_Gmail__update_message_labels", {}),
            ("mcp__claude_ai_Canva__generate-design", {"query": "revision slides"}),
            ("mcp__ultron__remember", {"text": "x"}),
            ("mcp__ultron__write_note", {"path": "Ultron/Plan.md"}),
            ("mcp__ultron__mark_important", {"path": "School"}),
        ]:
            self.assertFalse(registry.needs_ok(name, args), name)

    def test_people_and_unknown_tools_ask(self):
        for name, args in [
            ("mcp__claude_ai_Gmail__send_message", {}),
            ("mcp__claude_ai_Gmail__reply", {}),
            ("mcp__claude_ai_Gmail__forward", {}),
            ("mcp__claude_ai_Google_Calendar__respond_to_event", {}),
            ("mcp__claude_ai_Google_Calendar__create_event", {"attendees": ["a@b.com"]}),
            ("mcp__claude_ai_Google_Drive__share_file", {}),
            ("mcp__claude_ai_TickTick__assign_task", {}),
            ("mcp__claude_ai_Canva__publish-brand-template", {}),
            ("mcp__ultron__whatsapp_send", {}),
            ("mcp__ultron__unmark_important", {"path": "School"}),
            ("mcp__claude_ai_Supabase__execute_sql", {}),  # not an everyday connector
            ("Bash", {}),
        ]:
            self.assertTrue(registry.needs_ok(name, args), name)

    def test_important_files_ask(self):
        registry.important._save(["school/chemistry", "coursework"])
        self.assertTrue(registry.needs_ok("mcp__ultron__write_note", {"path": "School/Chemistry/Test.md"}))
        self.assertTrue(registry.needs_ok("mcp__ultron__write_note", {"path": "school/chemistry.md"}))
        self.assertFalse(registry.needs_ok("mcp__ultron__write_note", {"path": "School/Chemistry 2.md"}))
        # a Drive file by id, named in an earlier result
        registry.connectors.remember_items("mcp__claude_ai_Google_Drive__search_files", {"files": [{"id": "f9", "name": "Coursework"}]})
        self.assertTrue(registry.needs_ok("mcp__claude_ai_Google_Drive__trash_file", {"fileId": "f9"}))


if __name__ == "__main__":
    unittest.main()
