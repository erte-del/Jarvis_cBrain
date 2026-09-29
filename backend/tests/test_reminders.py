"""Reminders: TickTick reads run freely, changes ask; task cards.
    .venv/bin/python -m unittest tests.test_reminders
"""

import unittest

from tools import canvas, registry

TT = "mcp__claude_ai_TickTick__"


class RemindersTest(unittest.TestCase):
    def test_reads_run_freely_changes_ask(self):
        # Real tool names from the connector.
        for action in ["search_task", "filter_tasks", "get_task_by_id", "list_undone_tasks_by_time_query",
                       "list_undone_tasks_by_date", "list_projects", "get_user_preference", "fetch"]:
            self.assertEqual(registry.classify(TT + action), "read", action)
        for action in ["create_task", "batch_add_tasks", "complete_task", "update_task", "move_task", "delete_task",
                       "complete_tasks_in_project"]:
            self.assertEqual(registry.classify(TT + action), "act", action)

    def test_confirm_card_names_the_task(self):
        result = [{"type": "text", "text": '{"result":[{"id":"t1","projectId":"inbox1","title":"Call the bank",'
                   '"dueDate":"2026-09-30T05:00:00.000+0000"}]}'}]
        registry.connectors.remember_items(TT + "list_undone_tasks_by_time_query", result)
        _, _, details = registry.describe_call(TT + "complete_task", {"project_id": "inbox1", "task_id": "t1"})
        self.assertIn(["task", "Call the bank (2026-09-30T05:00:00.000+0000)"], details)
        # list_undone_tasks_* results spell it due_date.
        registry.connectors.remember_items(TT + "list_undone_tasks_by_date", [{"type": "text", "text":
            '{"result":[{"id":"t2","title":"Buy milk","due_date":"2026-10-05T18:00:00+0400"}]}'}])
        _, _, details = registry.describe_call(TT + "delete_task", {"project_id": "inbox1", "task_id": "t2"})
        self.assertIn(["task", "Buy milk (2026-10-05T18:00:00+0400)"], details)

    def test_create_card_shows_task_fields_as_rows(self):
        _, _, details = registry.describe_call(TT + "create_task", {
            "task": {"title": "Call the bank", "dueDate": "2026-09-30T09:00:00+04:00", "reminders": ["TRIGGER:PT0S"]},
            "client_timezone": "Asia/Dubai"})
        self.assertEqual(details, [["title", "Call the bank"], ["dueDate", "2026-09-30T09:00:00+04:00"],
                                   ["reminders", "TRIGGER:PT0S"], ["client timezone", "Asia/Dubai"]])

    def test_task_card(self):
        data = canvas._card_data({"kind": "tasks", "title": "Today", "items": [
            {"title": "Call the bank", "due": "Wed 30 Sep 09:00", "list": "Inbox", "done": False},
            {"title": "Buy milk", "done": True, "priority": "high"},  # unknown fields are dropped
        ]})
        self.assertEqual(data["items"], [
            {"title": "Call the bank", "due": "Wed 30 Sep 09:00", "list": "Inbox", "done": "False"},
            {"title": "Buy milk", "done": "True"},
        ])


if __name__ == "__main__":
    unittest.main()
