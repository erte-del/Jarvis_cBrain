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
- **Make images with AI.** Describe a picture and Jarvis paints it with FLUX.2 Klein
  running on this Mac (about 20 seconds, free, nothing leaves the machine). It can also
  change an image with AI ("make it snowy", "turn it into a watercolour", "put a hat on
  the dog"), each change as a new version. Set it up once with `scripts/setup_images.sh`
  (downloads about 16 GB, keeps 8 GB).
- **Make videos.** Describe a shot and Jarvis makes a short clip (up to 5 seconds,
  832×480, no sound) with Wan 2.1 running on this Mac: free, and nothing leaves the
  machine. It's slow (about 13 minutes for 5 seconds on an M5) and runs in the
  background, with progress on the canvas. It asks you first. Set it up once with
  `scripts/setup_video.sh` (downloads about 17.6 GB, keeps 14 GB). Text only for
  now: animating an existing image needs a bigger model.
- **Play music.** It plays songs, albums and playlists in the Spotify app on this Mac
  and controls playback (pause, next, volume, …). It can also list the songs in your own
  playlists, which needs a Spotify developer app (see `.env.example`).
- **Check your homework.** It reads your school's Microsoft Teams activity feed
  from Chrome on this Mac, where you're already signed in, and can tell you when a
  teacher sets something new. It also reads a class's posts, for assessment dates and
  topic lists. School accounts don't let apps read assignments, so
  this needs one Chrome setting (see `.env.example`).
- **Browse Amazon.** It searches Amazon and reads your orders, cart and wish lists in
  Chrome on this Mac, where you're already signed in (no password is stored). It can
  add to or remove from your cart, or add to your wish list, after you approve. It
  can't place an order: you check out in Chrome yourself. Uses the same Chrome setting
  as homework; set `JARVIS_AMAZON_URL` if you don't shop on amazon.ae.
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

**Always on (optional).** `scripts/autostart.sh on` starts Jarvis when you log in and
starts him again if he crashes; `scripts/autostart.sh off` undoes it. While it's on,
quitting `Jarvis.app` restarts Jarvis instead of stopping him (do that after changing
`.env`), and the log is `~/Library/Logs/Jarvis.log`. If macOS asks whether Python may
access your Desktop folder, allow it; a project kept outside Desktop and Documents is
never asked.

**On your phone (optional).** Jarvis has no password, so it never listens on your Wi-Fi.
Instead, [Tailscale](https://tailscale.com) connects your own devices privately: install
it on this Mac and your phone, run `tailscale serve --bg 8000` on the Mac, and put the
address it prints in `.env` as `JARVIS_REMOTE_ORIGIN` (see `.env.example`). Then open
that address on your phone, from anywhere, while this Mac is awake and Jarvis is running.

**Back up.** `scripts/backup.sh` writes everything of yours that isn't on GitHub (`.env`,
memory, saved chats, scheduled jobs, school notes, images, 3D models, videos, uploads) to
`~/Jarvis-backup-<date>.tgz`. `scripts/backup.sh restore FILE` puts it back, in this
project or in a fresh clone on another Mac. The file holds your keys: keep it to yourself.

**For development**, in two terminals (the page reloads as you edit):

    cd backend && .venv/bin/python main.py      # API on http://127.0.0.1:8000
    cd frontend && npm run dev                   # UI on http://127.0.0.1:5173

Then open http://127.0.0.1:5173.

To test the brain without the UI (`/haiku`, `/sonnet`, `/opus` switch models):

    cd backend && .venv/bin/python chat_cli.py

Tests:

    cd backend && .venv/bin/python -m unittest discover tests

## Move to a new Mac

**On the old Mac**

1. `scripts/backup.sh`, then copy `~/Jarvis-backup-<date>.tgz` to the new Mac (AirDrop or
   a USB stick; it holds your keys, so not by email).
2. `scripts/autostart.sh off` if autostart is on. Two running Jarvises would both run
   your scheduled jobs and text you twice.

**On the new Mac**

1. Install Claude Code and sign in with your Pro account, plus uv and Node 24 (see
   [Setup](#setup)). Install the apps you use Jarvis with: Google Chrome, Spotify,
   WhatsApp, Blender, Tailscale.
2. Clone the project into your home folder, not Desktop or Documents (macOS restricts
   those for background programs):

       git clone https://github.com/erte-del/Jarvis_cBrain.git ~/Jarvis_cBrain

3. Run the backend and frontend commands from [Setup](#setup). Skip copying
   `.env.example`: the backup brings your `.env`.
4. `scripts/backup.sh restore ~/Jarvis-backup-<date>.tgz`
5. `scripts/setup_images.sh` and `scripts/setup_video.sh`, if you want images and videos
   made on this Mac (about 34 GB of downloads, 22 GB kept).
6. `scripts/make_app.sh`, then open `Jarvis.app` once. It builds the page and starts Jarvis.

**Sign-ins and switches only you can do**

- **Chrome:** sign in to Teams and Amazon, then View → Developer → Allow JavaScript from
  Apple Events.
- **Spotify and WhatsApp:** sign in to the apps. WhatsApp also needs Jarvis allowed under
  System Settings → Privacy & Security → Accessibility.
- **Contacts:** add your Google account under System Settings → Internet Accounts, with
  Contacts on.
- **Tailscale:** sign in to the same account and run `tailscale serve --bg 8000`. The new
  Mac gets its own address: put that one in `.env` as `JARVIS_REMOTE_ORIGIN`.
- **Permission prompts:** the first time Jarvis uses Chrome, Spotify, Contacts or
  notifications, macOS asks. Allow each once.

Nothing to do for the claude.ai connectors (Gmail, Calendar, TickTick, …) and Telegram:
they come with your Claude login and your `.env`.

**If the new Mac should stay on all the time** (a Mac mini)

1. `scripts/autostart.sh on`
2. System Settings → Energy: turn on "Prevent automatic sleeping when the display is
   off" and "Start up automatically after a power failure".
3. System Settings → Users & Groups: set "Automatically log in as" to your user, so
   Jarvis comes back after a restart without anyone typing a password. This needs
   FileVault off, which means anyone who takes the Mac can read its disk.

**Check it worked.** Ask Jarvis what he remembers about you, open a saved chat and
continue it, ask for your homework, play a song, and open the page on your phone.

## How it fits together

    frontend/          React + Vite page: chat, canvas, 3D viewer, usage / log panels
    backend/main.py    FastAPI server: the /ws WebSocket, image, 3D and upload endpoints
    backend/brain/     the brain (Claude Code via the Agent SDK), router, prompts,
                       confirmation gate
    backend/scheduler.py, notify.py   jobs Jarvis runs on its own, and how their results reach you
    backend/tools/     Jarvis's own tools, served to Claude as an in-process MCP server,
                       each labelled read (runs freely) or act (asks you first)
    backend/storage/   images, 3D models, uploads, usage numbers, memory, scheduled jobs (all local files)
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
- [x] Phase 6: memory (`remember` / `recall` / `forget`, and the memory button in the top bar)
- [ ] Phase 7: polish (wake word, barge-in)
