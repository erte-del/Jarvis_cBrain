"""A session that started without the claude.ai connectors looks for them again."""

import unittest

from brain.brain_claudecode import ClaudeCodeBrain


class FakeClient:
    def __init__(self, names):
        self.names, self.closed = names, False

    async def get_mcp_status(self):
        return {"mcpServers": [{"name": n, "status": "connected"} for n in self.names]}

    async def disconnect(self):
        self.closed = True


class RetryConnectors(unittest.IsolatedAsyncioTestCase):
    async def run_retry(self, names):
        brain = ClaudeCodeBrain()
        brain.provider = "claude"
        brain._client = client = FakeClient(names)
        brain._has_connectors = False
        await brain._retry_connectors()
        return brain, client

    async def test_restarts_when_still_missing(self):
        brain, client = await self.run_retry(["ultron"])
        self.assertTrue(client.closed)
        self.assertIsNone(brain._client)

    async def test_keeps_session_when_they_arrived_late(self):
        brain, client = await self.run_retry(["ultron", "claude.ai Gmail"])
        self.assertFalse(client.closed)
        self.assertTrue(brain._has_connectors)

    async def test_waits_between_retries(self):
        brain, client = await self.run_retry(["ultron"])
        brain._client, brain._has_connectors = FakeClient(["ultron"]), False
        await brain._retry_connectors()  # too soon after the last try
        self.assertFalse(brain._client.closed)


if __name__ == "__main__":
    unittest.main()
