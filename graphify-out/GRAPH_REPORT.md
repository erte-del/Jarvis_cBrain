# Graph Report - Jarvis_cBrain  (2026-10-02)

## Corpus Check
- 140 files · ~80,907 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 4, .css 2, .example 1)

## Summary
- 1688 nodes · 3621 edges · 117 communities (70 shown, 47 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 135 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e31003cd`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- model_store.py
- ws.ts
- shapes.py
- image_ops.py
- image_store.py
- StoreTest
- package.json
- main.py
- web.py
- scheduler.py
- websocket_endpoint
- RouterTest
- FakeBrain
- compilerOptions
- Brain
- events.py
- compilerOptions
- config.py
- mac.py
- re
- ._connect
- spotify.py
- Locator
- Jarvis_cBrain
- asyncio
- job_store.py
- ApiBrain
- video.py
- .oxlintrc.json
- Jarvis
- Jarvis Frontend index.html (Vite entry, #root, /src/main.tsx)
- typing
- Favicon (glowing cyan orb)
- tsconfig.json
- start_jarvis.sh
- db.py
- memory_store.py
- voice/__init__.py
- stt.py
- tts.py
- vad.py
- make_app.sh
- stop_jarvis.sh
- Stage.tsx
- JobsTest
- registry.py
- textbook.py
- Canvas.tsx
- Chat.tsx
- storage/__init__.py
- TopBar.tsx
- notes.py
- canvas.py
- terminal.py
- slides.py
- App.tsx
- SidePanels.tsx
- chat_store.py
- youtube.py
- important.py
- Terminal.tsx
- Jarvis — Full Build Prompt
- models3d.py
- Trimesh
- Jarvis To-Do List
- GateTest
- HomeworkTest
- contacts.py
- floating_parts
- test_backup.py
- ContactsTest
- VideoTest
- phone.py
- whatsapp.py
- AmazonTest
- FakeClient
- ImageGenTest
- MemoryTest
- NotesTest
- run
- consult_expert
- telegram.py
- FlightsTest
- ClassifyTest
- UploadTest
- Model3DViewer.tsx
- now_note
- .can_use_tool
- upload
- NeedsOkTest
- SlidesTest
- TelegramTest
- YoutubeTest
- ask_expert
- _blender
- What Jarvis can do
- StartTest
- LoginTest
- ShapesTest
- SyllabusTest
- test_textbook.py
- FloatingTest
- NewShapesTest
- RemindersTest
- DueTest
- UsageNumbersTest
- push
- ChatStoreTest
- SmallChangesTest
- TerminalTest
- autostart.sh
- mcp/README.md
- backup.sh
- setup_images.sh
- setup_location.sh
- setup_video.sh
- itertools

## God Nodes (most connected - your core abstractions)
1. `ClaudeCodeBrain` - 29 edges
2. `websocket_endpoint()` - 22 edges
3. `emit()` - 21 edges
4. `Jarvis` - 20 edges
5. `compilerOptions` - 18 edges
6. `Done` - 17 edges
7. `_text()` - 17 edges
8. `EditError` - 17 edges
9. `react` - 16 edges
10. `Jarvis — Full Build Prompt` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Knowing you` --references--> `Jarvis`  [INFERRED]
  README.md → backend/brain/agent.py
- `11. Project structure` --references--> `error()`  [INFERRED]
  JARVIS_BUILD_PROMPT.md → backend/events.py
- `3. Contacts lookup  — *Priority 3*` --references--> `find_contact()`  [INFERRED]
  to_do_list.md → backend/tools/contacts.py
- `6. Notifications  — *Priority 5 (ships with the scheduler)*` --references--> `text_me()`  [INFERRED]
  to_do_list.md → backend/tools/telegram.py
- `Honorable mentions (later)` --references--> `youtube()`  [INFERRED]
  to_do_list.md → backend/tools/youtube.py

## Import Cycles
- None detected.

## Communities (117 total, 47 thin omitted)

### Community 0 - "model_store.py"
Cohesion: 0.20
Nodes (22): model_file(), 3D previews (.glb) and finished exports. Names are checked strictly., add_export(), add_version(), card_data(), create(), download_name(), Export (+14 more)

### Community 1 - "ws.ts"
Cohesion: 0.12
Nodes (21): ConfirmCardProps, STATUS_LABEL, Action, baseReducer(), BatteryManager, ChatState, ClientEvent, clip() (+13 more)

### Community 2 - "shapes.py"
Cohesion: 0.14
Nodes (24): apply_changes(), build_scene(), _linear(), _loft_sections(), _material(), Part, _points(), Any (+16 more)

### Community 3 - "image_ops.py"
Cohesion: 0.11
Nodes (30): OpsTest, Image, sample(), StoreTest, add_border(), add_text(), apply_all(), blur() (+22 more)

### Community 4 - "image_store.py"
Cohesion: 0.07
Nodes (56): add_version(), card_data(), create(), _dir(), file_path(), ImageRecord, load(), open_version() (+48 more)

### Community 6 - "package.json"
Cohesion: 0.06
Nodes (35): dependencies, react, react-dom, react-markdown, remark-gfm, @xterm/addon-fit, @xterm/xterm, devDependencies (+27 more)

### Community 7 - "main.py"
Cohesion: 0.08
Nodes (21): Jarvis logic: router -> brain -> events., ConfirmationGate, Event, Confirmation gate for 'act' tools. (Phase 4a) Claude Code runs 'read' tools…, Record your answer from the browser. False if nothing was waiting., Open questions, for a tab that connects while they're waiting., Jarvis's brain: talks to Claude., Pushes events to every open browser tab. Replies stream back on the tab that… (+13 more)

### Community 8 - "web.py"
Cohesion: 0.10
Nodes (21): PublicUrlTest, Web helper tests. Run from the backend folder: .venv/bin/python -m unittest…, SourcesTest, block_private_urls(), domain(), _is_public_ip(), is_public_url(), links_in_text() (+13 more)

### Community 9 - "scheduler.py"
Cohesion: 0.09
Nodes (29): Done, Error, Brain protocol + BrainEvent types. Everything in Jarvis talks to a `Brain`,…, A small piece of the reply text, streamed as it is generated., Claude started using a tool (e.g. a web search)., A tool finished. `data` is the tool's structured result, when there is one., The reply is complete. `model` is the full model ID that answered., TextDelta (+21 more)

### Community 10 - "websocket_endpoint"
Cohesion: 0.09
Nodes (36): conversation_new(), error(), notice(), connect(), disconnect(), emit(), Event, Sender (+28 more)

### Community 12 - "FakeBrain"
Cohesion: 0.14
Nodes (4): ExpertCanvasTest, FakeBrain, IdleStartOverTest, tab()

### Community 13 - "compilerOptions"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 14 - "Brain"
Cohesion: 0.14
Nodes (10): Brain, BrainEvent, Send one user message and stream back events until `Done` or `Error`., Forget the conversation and start a fresh one (optionally on another provider),…, Release resources (e.g. stop the Claude Code process)., 13. FIRST STEPS (start here), 1. Decision: how Jarvis talks to Claude, ❌ NOT USED (documented for later): Claude API with an API key (+2 more)

### Community 15 - "events.py"
Cohesion: 0.13
Nodes (23): Something for the frontend to show (canvas image, card, ...). Phase 4a+., UIEvent, The model the conversation is on now., canvas_card(), chats_list(), confirm_request(), confirm_resolved(), conversation_loaded() (+15 more)

### Community 16 - "compilerOptions"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "config.py"
Cohesion: 0.08
Nodes (25): Jarvis system prompt(s)., Settings loaded from .env., explain_error(), _find_omniroute(), _is_local(), OmniRoute (the optional gateway brain): is it running, start it, explain its…, Does anything answer at the gateway's address? (Any HTTP reply counts.), The omniroute command. Jarvis.app starts without your shell's PATH, so also… (+17 more)

### Community 18 - "mac.py"
Cohesion: 0.11
Nodes (37): Runs INSIDE Blender (never imported by Jarvis). Fixed script: Claude never…, Runs INSIDE Blender (never imported by Jarvis). Fixed script: Claude never…, find_app(), find_files(), _folder(), in_folder(), locator(), mac_change() (+29 more)

### Community 19 - "re"
Cohesion: 0.20
Nodes (13): _dicts(), is_read(), parse(), Any, claude.ai connectors (Gmail, Supabase, Canva, ...): read/act labels. Claude…, mcp__claude_ai_Gmail__search_threads' -> ('Gmail', 'search_threads'). None if…, Every dict inside a tool result; JSON text is parsed on the way., remember_items() (+5 more)

### Community 20 - "._connect"
Cohesion: 0.20
Nodes (8): Give slow connectors a moment, so the first message can already use them., Switch claude.ai connectors on or off to match JARVIS_CONNECTORS (.env). Claude…, The school notes as a paragraph for the system prompt ("" when there are none)., school_block(), Point Claude Code at the Pro login (provider "claude") or at the gateway. The…, set_login(), ClaudeAgentOptions, ClaudeSDKClient

### Community 21 - "spotify.py"
Cohesion: 0.08
Nodes (45): For urlopen to HTTPS sites: Python's own certificates plus the Mac keychain's,…, ssl_context(), MatchPlaylistTest, PhoneTest, Spotify helper tests. Run from the backend folder: .venv/bin/python -m unittest…, ToUriTest, _new_card_id(), Put a markdown card on the canvas from Jarvis's own code. Returns the card id. (+37 more)

### Community 22 - "Locator"
Cohesion: 0.08
Nodes (26): AppKit, Bool, CLLocation, CLLocationCoordinate2D, CLLocationManager, CLLocationManagerDelegate, CoreLocation, Date (+18 more)

### Community 23 - "Jarvis_cBrain"
Cohesion: 0.18
Nodes (10): claude-agent-sdk==0.2.160, fastapi / uvicorn, pillow, Backend Python Requirements, trimesh + geometry deps (numpy, shapely, mapbox-earcut, scipy, rtree), How it fits together, Jarvis_cBrain, Move to a new Mac (+2 more)

### Community 24 - "asyncio"
Cohesion: 0.09
Nodes (26): asyncio, Reaching you when you're not looking at the chat. One notification goes three…, Notifications since the user's last message, for Jarvis's conversation to know…, take_unseen(), Amazon: which pages it opens, which buttons it presses, never checkout. Chrome…, Saved chats: the 5-chat limit. Run from the backend folder: .venv/bin/python -m…, Contacts: relationship words, read-only label, errors. The Contacts app itself…, Homework: what's new, read-only label, errors. Chrome itself isn't touched.… (+18 more)

### Community 25 - "job_store.py"
Cohesion: 0.09
Nodes (42): jobs_list(), change_job(), jobs_event(), Something you did in the schedule panel., due(), loop(), quiet(), Run one job now and tell the user the result. Never raises. (+34 more)

### Community 27 - "video.py"
Cohesion: 0.10
Nodes (35): asset(), health(), Finished videos. Names are checked strictly., Spotify sends you back here after the login link Jarvis showed you., Image files for the canvas. Names are checked strictly, so only stored images…, spotify_callback(), video_file(), card_data() (+27 more)

### Community 28 - ".oxlintrc.json"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 29 - "Jarvis"
Cohesion: 0.09
Nodes (13): Jarvis, Event, A big conversation left alone for over an hour: Claude's cached copy has…, Answer one user message, yielding WebSocket events for the browser., Haiku / Sonnet / Opus selection. Order of checks: 1. The model picked in the UI…, Route, DeviceTest, send() (+5 more)

### Community 31 - "typing"
Cohesion: 0.11
Nodes (30): Flights: the search it opens, what it refuses. Chrome isn't touched.…, amazon_change(), amazon_read(), _open(), page_url(), Any, tool, Amazon: browse the user's account in Chrome on this Mac, where they're signed… (+22 more)

### Community 32 - "Favicon (glowing cyan orb)"
Cohesion: 0.67
Nodes (3): AI Core Orb Visual Identity, Favicon (glowing cyan orb), Radial Gradient g (cyan-to-teal)

### Community 36 - "memory_store.py"
Cohesion: 0.10
Nodes (36): change_memory(), An edit you made in the memory panel. ValueError with the reason if it can't be…, add(), _check(), delete(), entries(), label(), _luhn() (+28 more)

### Community 43 - "Stage.tsx"
Cohesion: 0.17
Nodes (18): Core(), SAMPLE, Stage(), StageProps, Terminal, VOICE_PILL, VOICE_STATES, Waveform() (+10 more)

### Community 44 - "JobsTest"
Cohesion: 0.09
Nodes (7): call(), MacTest, fake_run(), fake_open(), run(), skipUnless, JobsTest

### Community 45 - "registry.py"
Cohesion: 0.09
Nodes (22): item_label(), h5hdgf82...' -> 'Jarvis test (2026-09-30T16:00:00+04:00)', if Jarvis has seen…, _always_load(), auto_allowed(), describe_call(), friendly_name(), hooks(), JarvisTool (+14 more)

### Community 46 - "textbook.py"
Cohesion: 0.12
Nodes (22): _download(), find(), Any, tool, Syllabus: what the user's A-level exam boards say is on each course. The…, Indexes of the pages to show: the course overview without a query, else the…, syllabus(), _image() (+14 more)

### Community 47 - "Canvas.tsx"
Cohesion: 0.19
Nodes (18): Canvas(), CanvasProps, CardBody(), EmailList(), Events(), isUnread(), Item, MapCard() (+10 more)

### Community 48 - "Chat.tsx"
Cohesion: 0.18
Nodes (18): Chat(), ChatProps, CopyButton(), domain(), LongWait(), Message(), MicIcon(), ModelBadge() (+10 more)

### Community 49 - "storage/__init__.py"
Cohesion: 0.15
Nodes (13): Local storage: SQLite + assets/ folder., Files you upload from your computer. storage/uploads/upl_001/report.pdf Images…, Store a file and return its id (upl_001, ...)., save(), AI images, with fake mflux commands instead of FLUX. Run from the backend…, Image editing and storage tests (no network). Run from the backend folder:…, Uploads: the /upload endpoint and read_upload. Run from the backend folder:…, read_upload: open a file the user uploaded from their computer. (+5 more)

### Community 50 - "TopBar.tsx"
Cohesion: 0.21
Nodes (18): jobWhen(), MemoryMenu(), MemoryProps, RUN_STATUS, SavedChats(), ScheduleMenu(), Settings(), TopBar() (+10 more)

### Community 51 - "notes.py"
Cohesion: 0.24
Nodes (17): is_private(), _notes(), Any, Path, tool, search_notes / read_note / write_note: your Obsidian vault (JARVIS_VAULT in…, Write a note; returns its path in the vault. ValueError when it can't., The vault file a relative path names. ValueError if it leaves the vault or is… (+9 more)

### Community 52 - "canvas.py"
Cohesion: 0.20
Nodes (13): has_clients(), Calendar: Google Calendar reads run freely, writes ask; Jarvis knows the date;…, Reminders: TickTick reads run freely, changes ask; task cards. .venv/bin/python…, _card_data(), map_data(), open_terminal(), Any, tool (+5 more)

### Community 53 - "terminal.py"
Cohesion: 0.15
Nodes (13): WebSocket, /ws/terminal: a real shell in a canvas tab, for you to type in (e.g. to run…, Your normal environment, without the variables that point Jarvis's own Claude…, In the shell's process, before it starts: make the pty its terminal, so Ctrl-C…, _resize(), serve(), _shell_env(), _take_terminal() (+5 more)

### Community 54 - "slides.py"
Cohesion: 0.19
Nodes (14): build(), _fill(), _free(), make_slides(), Any, Path, tool, Slides: PowerPoint lessons in the style of the user's computing teacher. The… (+6 more)

### Community 55 - "App.tsx"
Cohesion: 0.27
Nodes (11): App(), PANE_IDS, PANES, Panel(), PanelProps, LogPanel(), TerminalPanel(), frontend_src_index (+3 more)

### Community 56 - "SidePanels.tsx"
Cohesion: 0.22
Nodes (14): COMMANDS, countdown(), fmt(), GatewayModels(), Meter(), MODELS, resetTime(), TerminalPanelProps (+6 more)

### Community 57 - "chat_store.py"
Cohesion: 0.21
Nodes (13): _clean(), _clean_cards(), delete(), load(), Saved chats (at most MAX_CHATS), in storage/chats.json. A saved chat is the…, Only what's needed to show the chat again; the browser sends the rest too., Newest first, without the messages., Save (or update) a chat. ValueError when it's new and MAX_CHATS are already… (+5 more)

### Community 58 - "youtube.py"
Cohesion: 0.22
Nodes (12): YouTube: the search it fetches, how it reads the page, what it refuses. Nothing…, _fetch(), Any, tool, youtube: search YouTube. (read) No API key: it fetches YouTube's own search…, YouTube's text objects: {'simpleText': ...} or {'runs': [{'text': ...}, ...]}., One line per video in the search page: link | title | channel | length | views…, _renderers() (+4 more)

### Community 59 - "important.py"
Cohesion: 0.32
Nodes (13): entries(), _listing(), mark_important(), matches(), normalize(), Any, tool, mark_important / unmark_important: files and folders Jarvis must ask about… (+5 more)

### Community 60 - "Terminal.tsx"
Cohesion: 0.22
Nodes (7): Terminal(), TerminalProps, API_BASE, JarvisSocket, useJarvis(), @xterm/addon-fit, @xterm/xterm

### Community 61 - "Jarvis — Full Build Prompt"
Cohesion: 0.14
Nodes (13): 0. Role and goal, 10. Memory, 11. Project structure, 2. Architecture, 5. Web search, 6. Connectors (Gmail, Calendar, Drive, …), 7. Canvas and images (the "dog picture" feature), 7b. 3D objects: preview mode (Phase 4d) (+5 more)

### Community 62 - "models3d.py"
Cohesion: 0.42
Nodes (12): _build_preview(), export_3d(), get_3d_spec(), _load(), preview_3d(), Any, tool, 3D objects: fast previews, changes through chat, final file only after… (+4 more)

### Community 63 - "Trimesh"
Cohesion: 0.21
Nodes (13): _loft(), _mesh(), Spin a [radius, height] profile around the vertical axis., A box with rounded corners: the hull of a small sphere in each corner., Points around a cross-section, from a rectangle (roundness 0) to an oval (1).…, Add `steps - 1` in-between sections: x linear (keeps order), the rest on a…, A smooth body through cross-sections placed along X (car bodies, hulls,…, _revolve() (+5 more)

### Community 64 - "Jarvis To-Do List"
Cohesion: 0.17
Nodes (11): maps(), Any, tool, 1. Calendar read/write  — *Priority 1*, 2. Reminders / tasks  — *Priority 2*, 3. Contacts lookup  — *Priority 3*, 6. Notifications  — *Priority 5 (ships with the scheduler)*, 8. Messaging + maps/travel  — *Priority 7* (+3 more)

### Community 67 - "contacts.py"
Cohesion: 0.29
Nodes (10): find_contact(), Any, tool, Contacts: look people up in macOS Contacts (read-only). There's no claude.ai…, my mom' -> 'mother', 'Annem' -> 'mother'. None if it isn't a relationship word., What to search for a relation, in order: the user's own word, English, Turkish,…, relation_label(), _run() (+2 more)

### Community 68 - "floating_parts"
Cohesion: 0.18
Nodes (11): _display_name(), floating_parts(), _gap(), (size [width, height, depth] in meters, triangle count)., 003m_mirror (mirrored)' -> 'mirror (mirrored)'., True if a and b touch, overlap, or one sits inside the other., Parts not connected to the main object, with their gap in meters. Parts count…, summary() (+3 more)

### Community 69 - "test_backup.py"
Cohesion: 0.31
Nodes (8): BackupTest, project(), Path, scripts/backup.sh: a backup made in one project folder restores into another.…, run(), sessions(), CompletedProcess, shutil

### Community 72 - "phone.py"
Cohesion: 0.42
Nodes (9): _call(), phone_taxi(), phone_volume(), Any, tool, The user's Android phone, through MacroDroid macros on it. (read: only their…, The address of the macro whose webhook identifier this is. ValueError if…, _text() (+1 more)

### Community 73 - "whatsapp.py"
Cohesion: 0.33
Nodes (9): phone_digits(), Any, tool, WhatsApp: send a message from the WhatsApp app on this Mac. (act: asks you…, +90 532 138 20 11' -> '905321382011'. None without a country code or if it…, _run(), _text(), _whatsapp_in_front() (+1 more)

### Community 79 - "run"
Cohesion: 0.28
Nodes (3): Run whatsapp_send with fake commands; front_apps is what's frontmost at each…, run(), WhatsAppTest

### Community 80 - "consult_expert"
Cohesion: 0.28
Nodes (9): consult_expert(), Any, From Claude Code's rate_limit_event. The numbers cover your whole Pro plan…, From a reply's ResultMessage.model_usage ({model: {inputTokens, ...}})., Everything the usage panel shows., record_limits(), record_turn(), _save() (+1 more)

### Community 81 - "telegram.py"
Cohesion: 0.36
Nodes (8): _call(), Any, tool, Telegram: Jarvis texts you from its own bot, which shows up on your phone as a…, Text your own chat (blocking). RuntimeError with the reason if it didn't go., send_text(), _text(), text_me()

### Community 85 - "Model3DViewer.tsx"
Cohesion: 0.32
Nodes (7): three, disposeObject(), frame(), Model3DViewer(), Viewer, Model3DData, three

### Community 86 - "now_note"
Cohesion: 0.29
Nodes (3): now_note(), Tuesday 29 September 2026, 20:15 CEST (UTC+0200)': local time with its offset., CalendarTest

### Community 87 - ".can_use_tool"
Cohesion: 0.29
Nodes (6): _Pending, Any, Called by Claude Code before any tool that isn't auto-allowed., PermissionResultAllow, PermissionResultDeny, ToolPermissionContext

### Community 88 - "upload"
Cohesion: 0.29
Nodes (7): fresh_page(), A file from your computer (the raw bytes as the body). Images go on the canvas;…, The page itself must never come from the browser's cache, or a rebuilt Jarvis…, upload(), middleware, post, Request

### Community 93 - "ask_expert"
Cohesion: 0.33
Nodes (7): ask_expert(), tool, 3. Model routing (cheap by default, strong when needed), Claude on your Pro login (the default), OmniRoute (optional), Talking and thinking, The brains

### Community 94 - "_blender"
Cohesion: 0.33
Nodes (7): _blender(), _contact_sheet(), Path, The four views in a 2×2 grid with labels, as a JPEG for Claude., Four quick views of a preview for Claude to look at, or None if Blender isn't…, Run one of Jarvis's fixed Blender scripts in the background. Returns Blender's…, render_views()

### Community 95 - "What Jarvis can do"
Cohesion: 0.29
Nodes (7): Doing things on its own, Knowing you, Making things, Messages, On this Mac, What Jarvis can do, Your accounts

### Community 96 - "StartTest"
Cohesion: 0.53
Nodes (3): dict, object, StartTest

### Community 97 - "LoginTest"
Cohesion: 0.47
Nodes (3): LoginTest, dict, object

### Community 106 - "push"
Cohesion: 0.50
Nodes (4): _mac(), push(), Tell the user something. A channel that fails is logged, never raised., configured()

## Knowledge Gaps
- **129 isolated node(s):** `$schema`, `plugins`, `react/rules-of-hooks`, `react/only-export-components`, `name` (+124 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 635 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **47 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ClaudeCodeBrain` connect `scheduler.py` to `main.py`, `FakeClient`, `MemoryTest`, `events.py`, `._connect`, `asyncio`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Why does `VideoTest` connect `VideoTest` to `asyncio`?**
  _High betweenness centrality (0.020) - this node is a cross-community bridge._
- **Why does `YoutubeTest` connect `YoutubeTest` to `youtube.py`?**
  _High betweenness centrality (0.017) - this node is a cross-community bridge._
- **What connects `$schema`, `plugins`, `react/rules-of-hooks` to the rest of the system?**
  _129 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `ws.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.1225296442687747 - nodes in this community are weakly interconnected._
- **Should `shapes.py` be split into smaller, more focused modules?**
  _Cohesion score 0.14 - nodes in this community are weakly interconnected._
- **Should `image_ops.py` be split into smaller, more focused modules?**
  _Cohesion score 0.1101010101010101 - nodes in this community are weakly interconnected._