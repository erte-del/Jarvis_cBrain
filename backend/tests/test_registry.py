"""Read/act labels. Run from the backend folder:
    .venv/bin/python -m unittest discover tests

If a tool is labelled 'read' it runs without asking you, so these tests matter.
"""

import unittest

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
        self.assert_kind("act", ["Bash", "Write", "mcp__some_local_server__get_secrets", "mcp__jarvis__unknown"])

    def test_builtins_and_own_tools(self):
        self.assert_kind("read", ["WebSearch", "WebFetch", "ToolSearch",
                                  "mcp__jarvis__ask_expert", "mcp__jarvis__show_on_canvas"])

    def test_friendly_names(self):
        self.assertEqual(registry.friendly_name("mcp__claude_ai_Gmail__send_message"), "Gmail: Send message")
        self.assertEqual(registry.friendly_name("mcp__claude_ai_Claude_Docs__query"), "Claude Docs: Query")
        self.assertEqual(registry.friendly_name("mcp__claude_ai_Canva__search-designs"), "Canva: Search designs")
        self.assertEqual(registry.friendly_name("mcp__jarvis__show_on_canvas"), "Show on canvas")

    def test_confirmation_details_are_readable(self):
        title, _, details = registry.describe_call(
            "mcp__claude_ai_Gmail__create_draft", {"to": ["a@b.com", "c@d.com"], "subject": "Hi"}
        )
        self.assertEqual(title, "Gmail: Create draft")
        self.assertEqual(details, [["to", "a@b.com, c@d.com"], ["subject", "Hi"]])


if __name__ == "__main__":
    unittest.main()
