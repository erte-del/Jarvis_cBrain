"""OmniRoute start-up tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import os
import unittest
from unittest import mock

import config
import gateway


@mock.patch.object(gateway, "_find_omniroute", return_value="/nvm/bin/omniroute")
@mock.patch.object(gateway, "running", return_value=True)
@mock.patch.object(gateway.subprocess, "Popen")
class StartTest(unittest.TestCase):
    @mock.patch.object(config, "GATEWAY_URL", "http://localhost:20128")
    @mock.patch.dict(os.environ, {"ANTHROPIC_AUTH_TOKEN": "x", "ANTHROPIC_BASE_URL": "http://y"})
    def test_starts_on_this_mac_only(self, popen, running, find):
        self.assertIsNone(gateway.start())
        args, kwargs = popen.call_args
        self.assertEqual(args[0][:3], ["/nvm/bin/omniroute", "serve", "--daemon"])
        self.assertEqual(kwargs["env"]["OMNIROUTE_SERVER_HOST"], "127.0.0.1")
        # None of Jarvis's Anthropic settings leak into OmniRoute.
        self.assertFalse([k for k in kwargs["env"] if k.startswith("ANTHROPIC_")])
        self.assertTrue(kwargs["env"]["PATH"].startswith("/nvm/bin"))

    @mock.patch.object(config, "GATEWAY_URL", "https://gateway.example.com")
    def test_never_starts_for_a_remote_address(self, popen, running, find):
        self.assertIn("isn't reachable", gateway.start())
        popen.assert_not_called()

    @mock.patch.object(config, "GATEWAY_URL", "http://localhost:20128")
    def test_not_installed(self, popen, running, find):
        find.return_value = None
        self.assertIn("npm i -g omniroute", gateway.start())
        popen.assert_not_called()


class ExplainTest(unittest.TestCase):
    def test_error_says_what_to_do(self):
        text = gateway.explain_error("bad_gateway: no provider")
        self.assertIn("bad_gateway: no provider", text)
        self.assertIn("Providers", text)


if __name__ == "__main__":
    unittest.main()
