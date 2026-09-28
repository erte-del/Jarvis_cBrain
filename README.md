# Jarvis_cBrain

Personal AI assistant with Claude as the brain. Runs locally, for one user only.
See `JARVIS_BUILD_PROMPT.md` for the full plan.

Jarvis talks to Claude through Claude Code (Claude Agent SDK), signed in with a
Claude Pro account. No API key is used.

## Setup

Requirements: Claude Code signed in with your Pro account (`claude auth status`
shows `"subscriptionType": "pro"`), [uv](https://docs.astral.sh/uv/), and Node 24.

Backend (Python 3.13 via uv):

    uv venv --python 3.13 backend/.venv
    VIRTUAL_ENV=backend/.venv uv pip install -r backend/requirements.txt

Frontend (Node 24 via nvm):

    cd frontend && npm install

Copy `.env.example` to `.env`. Never add an `ANTHROPIC_API_KEY`: Jarvis uses the Claude Pro login.

## Run

In two terminals:

    cd backend && .venv/bin/python main.py      # API on http://127.0.0.1:8000
    cd frontend && npm run dev                   # UI on http://127.0.0.1:5173

Open http://127.0.0.1:5173. Each reply shows a badge with the model that answered.

To test the brain without the UI:

    cd backend && .venv/bin/python chat_cli.py

## Status

- [x] Phase 1: text chat on the Pro subscription
- [ ] Phase 2: model router (Haiku / Sonnet / Opus, `ask_expert`)
- [ ] Phase 3: web search
- [ ] Phase 4: canvas and images
- [ ] Phase 5: voice
- [ ] Phase 6: connectors + confirmation gate
- [ ] Phase 7: memory
- [ ] Phase 8: polish (wake word, barge-in, desktop app)
