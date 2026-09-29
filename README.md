# Jarvis_cBrain

A personal AI assistant with Claude as its brain. It runs on your own Mac, for one user,
in a browser page with a chat on the left, a canvas in the middle and status panels on
the right. The backend only listens on 127.0.0.1, so nothing outside this machine can
reach it.

See `JARVIS_BUILD_PROMPT.md` for the original plan.

## What Jarvis can do

- **Chat.** Replies stream in word by word. Each reply shows a badge with the model
  that answered and why it was picked.
- **Search the web.** Uses Claude's built-in WebSearch and WebFetch tools. Answers end
  with the pages they came from, shown as clickable source chips. WebFetch can't reach
  this machine or your local network.
- **Show things on the canvas.** Tables, comparisons, drafts, plans, email lists and
  calendar events go on cards next to the chat, so the chat reply stays short.
- **Use your claude.ai connectors** (Gmail, Calendar, Drive, Canva, Spotify, …), the
  same ones enabled on your Claude account. Tools that only read (search, list, get)
  run freely. Anything that sends, deletes, creates or changes something shows a
  confirmation card first, and nothing happens until you approve it.
- **Find and edit images.** It finds photos on Pexels and edits them locally: crop,
  resize, rotate, flip, brightness, contrast, saturation, sharpen, blur, grayscale,
  sepia, text and borders. Every edit is a new version, so you can always go back.
  Click an image to select it, and "this one" in your next message means that image.
- **Build 3D objects.** Jarvis makes a quick preview you can spin around, then checks
  4 rendered views of its own work and fixes mistakes. When you're happy, Blender builds
  the final file (.blend, .fbx, .obj, .stl, .gltf or .glb), after you approve.
- **Make videos.** Describe a shot and Jarvis makes a short clip (up to 5 seconds,
  832×480, no sound) with Wan 2.1 running on this Mac: free, and nothing leaves the
  machine. It's slow (about 13 minutes for 5 seconds on an M5) and runs in the
  background, with progress on the canvas. It asks you first. Set it up once with
  `scripts/setup_video.sh` (downloads about 17.6 GB, keeps 14 GB). Text only for
  now: animating an existing image needs a bigger model.
- **Play music.** It plays songs, albums and playlists in the Spotify app on this Mac
  and controls playback (pause, next, volume, …). It can also list the songs in your own
  playlists, which needs a Spotify developer app (see `.env.example`).
- **Read your files.** Click 📎 in the chat box or drop files onto it. Images go on
  the canvas, where they can be edited. Text, code, CSV, JSON and PDF files are read
  as text (up to about 100K characters each). Files are kept in
  `backend/storage/uploads/`.
- **Consult an expert.** For hard problems (multi-step reasoning, tricky maths, complex
  code, long writing) Sonnet hands the task to Opus with `ask_expert`. Long answers go
  straight onto the canvas.
- **Track your usage.** The right-hand panel shows how much of your Pro plan's 5-hour and
  weekly limits is used, when they reset, and how many tokens Jarvis itself used.

## The brains

Jarvis has two brains. Switch between them with the gear icon at the top right.
Switching starts a new chat.

### Claude on your Pro login (the default)

Jarvis talks to Claude through Claude Code (the Claude Agent SDK), signed in with your
Claude Pro account. **No API key is used**: if an `ANTHROPIC_API_KEY` were set, Claude
Code would bill that key instead, so Jarvis removes it from its environment.

A router picks the model for each message:

1. A model you pick in the usage panel always wins.
2. Words in the message: "use opus" or "think hard" → **Opus**; "quick" or "use haiku" → **Haiku**.
3. Small talk stays on the current model.
4. Everything else → **Sonnet**, which can call `ask_expert` to consult Opus.

Switching models means sending the whole conversation to the new model again, so once a
conversation is big, the router won't move it to a cheaper model by itself. A big
conversation left alone for an hour starts over fresh, because Claude's cached copy of
it has expired (`JARVIS_NEW_CHAT_AFTER_IDLE_MIN`).

Jarvis is an assistant, not a coding agent: Claude Code's file, shell and sub-agent tools
are switched off. Jarvis only gets web search, tool search (so connector tools load on
demand) and its own tools.

### OmniRoute (optional)

[OmniRoute](https://github.com/diegosouzapw/OmniRoute) is a local gateway to other
providers' models (Gemini, Groq, …). It doesn't use your Pro limit. Install it with
`npm i -g omniroute`, then pick it with the gear icon: Jarvis starts it if it isn't
running (on 127.0.0.1 only). Connect at least one provider in its dashboard
(http://localhost:20128 → Providers). Its keyless free providers mostly refuse
requests from outside their own apps.

The models you can switch between are set in `JARVIS_GATEWAY_MODELS` and appear as
buttons in the usage panel. In OmniRoute mode:
- the claude.ai connectors are off, so your emails never go to other providers' models
- web search and `ask_expert` are off (web page reading still works)
- other models may use Jarvis's tools less reliably

## Setup

Requirements: Claude Code signed in with your Pro account (`claude auth status` shows
`"subscriptionType": "pro"`), [uv](https://docs.astral.sh/uv/), and Node 24.
Optional: Blender (for final 3D files) and the Spotify desktop app.

Backend (Python 3.13):

    uv venv --python 3.13 backend/.venv
    VIRTUAL_ENV=backend/.venv uv pip install -r backend/requirements.txt

Frontend:

    cd frontend && npm install

Copy `.env.example` to `.env` and fill in what you need. Every setting is explained
there: the Pexels key for images, Spotify, the Blender path, how hard Claude thinks
(`JARVIS_EFFORT`), which connectors to load (`JARVIS_CONNECTORS`) and the OmniRoute
settings. Never add an `ANTHROPIC_API_KEY`.

## Run

**The easy way: Jarvis.app.** Build it once:

    scripts/make_app.sh

Then double-click `Jarvis.app` (drag it to the Dock or Applications if you like). It
starts Jarvis and opens it in your browser at http://127.0.0.1:8000. Quit it from the
Dock to stop Jarvis. Logs go to `backend/storage/jarvis.log`. Run `make_app.sh` again
if you move the project folder.

**For development**, in two terminals (the page reloads as you edit):

    cd backend && .venv/bin/python main.py      # API on http://127.0.0.1:8000
    cd frontend && npm run dev                   # UI on http://127.0.0.1:5173

Then open http://127.0.0.1:5173.

To test the brain without the UI (`/haiku`, `/sonnet`, `/opus` switch models):

    cd backend && .venv/bin/python chat_cli.py

Tests:

    cd backend && .venv/bin/python -m unittest discover tests

## How it fits together

    frontend/          React + Vite page: chat, canvas, 3D viewer, usage / log panels
    backend/main.py    FastAPI server: the /ws WebSocket, image, 3D and upload endpoints
    backend/brain/     the brain (Claude Code via the Agent SDK), router, prompts,
                       confirmation gate
    backend/tools/     Jarvis's own tools, served to Claude as an in-process MCP server,
                       each labelled read (runs freely) or act (asks you first)
    backend/storage/   images, 3D models, uploads, usage numbers (all local files)
    scripts/           builds and runs Jarvis.app

## Status

- [x] Phase 1: text chat on the Pro subscription
- [x] Phase 2: model router (Haiku / Sonnet / Opus, `ask_expert`)
- [x] Phase 3: web search
- [x] Phase 4: abilities
  - [x] confirmation gate + canvas
  - [x] claude.ai connectors (Gmail, Calendar, Drive, …)
  - [x] images (search + edit)
  - [x] 3D objects
  - [x] Spotify
  - [x] OmniRoute as a second brain
  - [x] file uploads
- [ ] Phase 5: voice (the mic button and voice mode are only the interface so far)
- [ ] Phase 6: memory (Jarvis doesn't remember anything between chats yet)
- [ ] Phase 7: polish (wake word, barge-in)
