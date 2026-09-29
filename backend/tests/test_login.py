"""Login choice tests. Run from the backend folder:
    .venv/bin/python -m unittest discover tests
"""

import os
import unittest
from unittest import mock

import config

GATEWAY_VARS = {"ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN", *config._MODEL_VARS}


class LoginTest(unittest.TestCase):
    @mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-x", "ANTHROPIC_BASE_URL": "http://x"})
    def test_pro_login_clears_api_vars(self):
        config.set_login("claude")
        for var in config._API_AUTH_VARS:
            self.assertNotIn(var, os.environ)

    @mock.patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-x"})
    @mock.patch.object(config, "GATEWAY_URL", "http://localhost:20128")
    @mock.patch.object(config, "GATEWAY_KEY", "")
    def test_gateway_sets_url_token_and_models(self):
        config.set_login("omniroute")
        self.assertEqual(os.environ["ANTHROPIC_BASE_URL"], "http://localhost:20128")
        # A token must be set, or Claude Code would send the Pro login's token to the gateway.
        self.assertTrue(os.environ["ANTHROPIC_AUTH_TOKEN"])
        self.assertNotIn("ANTHROPIC_API_KEY", os.environ)
        self.assertEqual(os.environ["ANTHROPIC_DEFAULT_SONNET_MODEL"], config.GATEWAY_MODEL)

    @mock.patch.dict(os.environ, {})
    def test_switching_back_to_claude_removes_everything(self):
        config.set_login("omniroute")
        config.set_login("claude")
        self.assertFalse(GATEWAY_VARS & set(os.environ))


if __name__ == "__main__":
    unittest.main()
