"""Usage: starting over after a long break, expert answers on the canvas, the usage panel numbers.
Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

import hub
import usage
from brain.agent import Jarvis
from brain.base import Done
from tools import expert


class FakeBrain:
    def __init__(self, context_tokens: int, idle_min: float) -> None:
        self.provider = "claude"
        self.model = "sonnet"
        self.context_tokens = context_tokens
        self.last_active = time.time() - idle_min * 60
        self.new_conversations = 0

    async def send(self, text, images=None, model="sonnet"):
        yield Done("claude-sonnet-5")

    async def new_conversation(self, provider=None) -> None:
        self.new_conversations += 1
        self.context_tokens = 0

    async def close(self) -> None:
        pass


class IdleStartOverTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.seen: list[dict] = []

        async def tab(ev):
            self.seen.append(ev)

        self.tab = tab
        hub.connect(tab)

    async def asyncTearDown(self):
        hub.disconnect(self.tab)

    async def run_turn(self, brain: FakeBrain) -> None:
        async for _ in Jarvis(brain).handle_text("and the weather?"):
            pass

    async def test_big_conversation_after_long_break_starts_over(self):
        brain = FakeBrain(context_tokens=50_000, idle_min=90)
        await self.run_turn(brain)
        self.assertEqual(brain.new_conversations, 1)
        self.assertIn({"type": "conversation.new", "reason": "idle"}, self.seen)

    async def test_keeps_going_otherwise(self):
        for tokens, idle in [(50_000, 20), (8_000, 90)]:  # short break / small conversation
            brain = FakeBrain(context_tokens=tokens, idle_min=idle)
            await self.run_turn(brain)
            self.assertEqual(brain.new_conversations, 0, (tokens, idle))

    async def test_first_message_never_starts_over(self):
        brain = FakeBrain(context_tokens=50_000, idle_min=0)
        brain.last_active = 0.0
        await self.run_turn(brain)
        self.assertEqual(brain.new_conversations, 0)


class ExpertCanvasTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.seen: list[dict] = []

        async def tab(ev):
            self.seen.append(ev)

        self.tab = tab
        hub.connect(tab)

    async def asyncTearDown(self):
        hub.disconnect(self.tab)

    async def ask(self, answer: str) -> str:
        with mock.patch.object(expert, "consult_expert", mock.AsyncMock(return_value=answer)):
            result = await expert.ask_expert.handler({"task": "plan my week"})
        return result["content"][0]["text"]

    async def test_long_answer_goes_on_the_canvas(self):
        answer = "A detailed plan. " * 100
        text = await self.ask(answer)
        cards = [e for e in self.seen if e["type"] == "canvas.card"]
        self.assertEqual(len(cards), 1)
        self.assertEqual(cards[0]["data"]["content"], answer)
        self.assertIn("Don't repeat it", text)
        self.assertIn(cards[0]["id"], text)

    async def test_short_answer_stays_in_chat(self):
        text = await self.ask("42")
        self.assertEqual(text, "42")
        self.assertFalse([e for e in self.seen if e["type"] == "canvas.card"])


class UsageNumbersTest(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        patches = [
            mock.patch.object(usage, "FILE", Path(folder.name) / "usage.json"),
            mock.patch.object(usage, "windows", {}),
            mock.patch.object(usage, "_turns", []),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def test_plan_windows_from_claude_code(self):
        resets = int(time.time()) + 3600
        usage.record_limits({
            "status": "allowed",
            "rateLimitType": "five_hour",
            "unifiedWindows": {
                "five_hour": {"utilization": 0.16, "resetsAt": resets},
                "seven_day": {"utilization": 0.02, "resetsAt": resets + 86400},
            },
        })
        snap = usage.snapshot("claude", 1234)
        self.assertEqual(snap["windows"]["five_hour"], {"used": 0.16, "resets_at": resets})
        self.assertEqual(snap["windows"]["seven_day"]["used"], 0.02)
        self.assertEqual(snap["context_tokens"], 1234)

    def test_a_window_that_reset_is_back_to_zero(self):
        usage.record_limits({"unifiedWindows": {"five_hour": {"utilization": 0.9, "resetsAt": 1000}}})
        self.assertEqual(usage.snapshot("claude", 0)["windows"]["five_hour"]["used"], 0.0)

    def test_jarvis_tokens_count_only_this_window_and_survive_a_restart(self):
        usage._turns.append([time.time() - 6 * 3600, "claude-sonnet-5", 999, 999, 999, 999])  # older
        usage.record_turn({"claude-sonnet-5": {"inputTokens": 10, "cacheCreationInputTokens": 200,
                                               "cacheReadInputTokens": 3000, "outputTokens": 40}})
        tokens = usage.snapshot("claude", 0)["tokens"]
        self.assertEqual(tokens, {"input": 10, "cache_write": 200, "cache_read": 3000, "output": 40})
        usage._turns.clear()
        usage._load()  # like a restart
        self.assertEqual(usage.snapshot("claude", 0)["tokens"]["output"], 40)


if __name__ == "__main__":
    unittest.main()
