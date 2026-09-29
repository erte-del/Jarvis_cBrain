"""Tiny terminal chat for testing the brain without the web UI.

Run from the backend folder:
    .venv/bin/python chat_cli.py

Commands: /haiku, /sonnet, /opus to switch model, /quit to exit.
"""

import asyncio
import logging

from brain.base import Done, Error, TextDelta, ToolStart
from brain.brain_claudecode import ClaudeCodeBrain
from config import GATEWAY_URL


async def main() -> None:
    brain = ClaudeCodeBrain()
    model = "sonnet"
    print("Jarvis terminal chat. /haiku /sonnet /opus to switch model, /quit to exit.\n")
    try:
        while True:
            try:
                text = (await asyncio.to_thread(input, "you> ")).strip()
            except EOFError:
                break
            if not text:
                continue
            if text == "/quit":
                break
            if text in ("/haiku", "/sonnet", "/opus"):
                model = text[1:]
                print(f"(model -> {model})\n")
                continue

            print("jarvis> ", end="", flush=True)
            async for ev in brain.send(text, model=model):
                if isinstance(ev, TextDelta):
                    print(ev.text, end="", flush=True)
                elif isinstance(ev, ToolStart):
                    print(f"\n  [tool: {ev.name}]", flush=True)
                elif isinstance(ev, Done):
                    # "none" = no API key in use, i.e. Claude Code is on the Pro login.
                    if brain.provider == "omniroute":
                        auth = f"gateway {GATEWAY_URL}"
                    else:
                        auth = "Pro login" if brain.auth_source == "none" else f"API KEY? ({brain.auth_source})"
                    print(f"\n  [{ev.model} | {auth}]\n")
                elif isinstance(ev, Error):
                    print(f"\n  [error: {ev.message}]\n")
    finally:
        await brain.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    asyncio.run(main())
