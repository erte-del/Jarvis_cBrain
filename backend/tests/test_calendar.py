"""Calendar: Google Calendar reads run freely, writes ask; Jarvis knows the date; event cards.
    .venv/bin/python -m unittest tests.test_calendar
"""

import unittest

from brain.agent import now_note
from tools import canvas, registry

CAL = "mcp__claude_ai_Google_Calendar__"


class CalendarTest(unittest.TestCase):
    def test_reads_run_freely_writes_ask(self):
        for action in ["list_events", "get_event", "search_events", "list_calendars", "suggest_time"]:
            self.assertEqual(registry.classify(CAL + action), "read", action)
        for action in ["create_event", "update_event", "delete_event", "respond_to_event"]:
            self.assertEqual(registry.classify(CAL + action), "act", action)

    def test_now_note_has_date_and_offset(self):
        self.assertRegex(now_note(), r"^\w+day \d{2} \w+ \d{4}, \d{2}:\d{2} .*\(UTC[+-]\d{4}\)$")

    def test_confirm_card_names_the_event(self):
        # Shape of a real search_events result: JSON text inside the MCP content blocks.
        result = [{"type": "text", "text": '{"events":[{"id":"ev1","summary":"Jarvis test",'
                   '"start":{"dateTime":"2026-09-30T16:00:00+04:00"}}]}'}]
        registry.connectors.remember_events(CAL + "search_events", result)
        _, _, details = registry.describe_call(CAL + "delete_event", {"eventId": "ev1"})
        self.assertIn(["event", "Jarvis test (2026-09-30T16:00:00+04:00)"], details)
        _, _, details = registry.describe_call(CAL + "delete_event", {"eventId": "unknown"})
        self.assertEqual([d[0] for d in details], ["eventId"])

    def test_event_card_joins_attendees(self):
        data = canvas._card_data({"kind": "events", "title": "Today", "items": [
            {"title": "Standup", "start": "09:00", "attendees": ["Sarah", "Tom"], "location": ""},
        ]})
        self.assertEqual(data["items"], [{"title": "Standup", "start": "09:00", "attendees": "Sarah, Tom"}])


if __name__ == "__main__":
    unittest.main()
