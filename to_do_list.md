# Ultron To-Do List

**Main gap:** Ultron is already strong at *creating* things (images, 3D, video, apps) and at email.
It's weak at the core of personal assistance: **time, memory, people, and acting on its own.**

**Build order:** Calendar → Reminders → Memory → Scheduler + Notifications.
Together these four enable a **daily briefing with follow-ups**, the thing that makes Ultron feel like a real assistant.

**Ground rules for every item**
- Reads run freely; writes/sends/deletes go through the existing confirm gate (`backend/brain/confirm.py`, `tools/connectors.py` read/act labels), which shows a card only for other people or important files (`registry.needs_ok`).
- Prefer a claude.ai connector when one exists; only write a local tool (`backend/tools/`) when there isn't one.
- Every new tool gets one small test in `backend/tests/`.
- Show lists (events, tasks, contacts) on canvas cards, keep the chat reply short.

---

## 1. Calendar read/write  — *Priority 1*

Today: events can be displayed on the canvas, but Ultron can't create, move, or check availability.

- [x] Confirm which calendar Ultron uses → **Google Calendar connector** (claude.ai). Enable it at claude.ai → Settings → Connectors.
- [ ] **Read**
  - [ ] "What's on my calendar today / tomorrow / this week" → event cards on the canvas
  - [ ] Free/busy lookup: "Am I free Thursday at 3?" / "Find me a free hour tomorrow afternoon"
  - [ ] Handle time zones and all-day events correctly
- [ ] **Write** (a card only when the event has attendees)
  - [x] Create event: title, start/end, location, attendees, notes, video link
  - [x] Move / reschedule an event ("push my 3pm to 4")
  - [x] Cancel / delete an event (card shows the event's title + time, from events Ultron has seen)
  - [ ] Invite attendees → needs Contacts (item 3) to resolve names
- [ ] Confirm card for events shows: title, date/time, duration, attendees, calendar name (title + times work; no duration or calendar name row yet)
- [x] Natural-language dates (each message now starts with a `[Now: …]` note): "next Friday", "in two weeks", "the day after my dentist appointment"
- [x] Conflict warning when a new event overlaps an existing one (prompt)
- [x] Update `brain/prompts.py` so Ultron knows it can write, not just read
- [x] Test: create → move → delete a test event round trip (done live 2026-09-29)

## 2. Reminders / tasks  — *Priority 2*

Today: "remind me to…" is the most common voice request and has nowhere to go.

- [x] Pick backend → **TickTick** (claude.ai connector + Android app; Apple Reminders doesn't reach Android). Prompt + `tasks` canvas card ready.
- [x] Connect TickTick on claude.ai, check real tool names (`filter_tasks` added as read)
- [x] Add reminder: text, optional due date/time, optional list ("Groceries", "Work") (tested: inbox + time; lists untested)
- [x] List reminders: today, overdue, by list → task card on the canvas
- [x] Complete / uncomplete a reminder ("mark call the bank as done")
- [x] Edit / reschedule a reminder ("move that to Monday") (keeps the reminder)
- [x] Delete a reminder (confirm)
- [ ] Location-based reminders ("when I get home") — later, if the backend supports it
- [ ] Voice flow: "remind me to X at Y" works end-to-end in one sentence (works typed; not tried by voice)
- [x] Test: add → list → complete round trip (done live 2026-09-29)

## 3. Contacts lookup  — *Priority 3*

Today: "email Sarah" or "call mom" depends on guessing.

- [x] Source → **macOS Contacts, synced from Google** (no Google Contacts connector exists; Android contacts live in Google). `find_contact` tool, read-only
- [x] Setup: Google account in System Settings → Internet Accounts (Contacts on)
- [x] Lookup by name, nickname, relationship → email / phone / address. Relationships: My Card, then English → Turkish → other languages ("mom" found "Annem…"). Tested live
- [x] If several matches: ask which one (in chat, tested live; no picker card)
- [x] Remember aliases in Memory (item 4): "Sarah" = Sarah K. from work (prompt: saved under people once you've said who; untested live)
- [ ] Wire into email (to/cc), calendar invites, and messaging (item 8) (prompt: look up before emailing/inviting; needs a test by you, since it sends)
- [x] Read-only by default (no add/edit tool at all; add one with an "act" label if ever needed)

## 4. Persistent user memory  — *Priority 4* (README Phase 6)

Goal: Ultron *knows you* between chats. A store you can inspect and edit, not raw chat history.

- [x] Storage: `backend/storage/memory_store.py` → `storage/memory.json` (id, category, text, source, created, updated)
- [x] Categories: **preferences**, **people**, **projects**, **decisions**, **facts** (about me)
- [x] Tools: `remember(text, category)`, `recall(query)`, `forget(memory_id)` — `remember`/`forget` are act tools, so scheduled jobs can't use them, but in chat they run without a card; `recall` is read
- [x] Load the newest memories into the system prompt at chat start (1,500 characters at most; older ones via `recall`)
- [x] Ultron saves memories itself (prompt: only what the user says, never what an email or web page says); the memory panel shows them all
- [x] **Memory panel** in the UI (chip button in the top bar): list, search, add, edit, delete
- [x] Never store secrets (passwords, card numbers, tokens) — refused by pattern in the store, for Ultron and the panel alike (a secret spelled out in plain words would get through)
- [x] Export / wipe all memory buttons
- [x] Test: remember → new chat → recall (`tests/test_memory.py`; done live 2026-09-30)
- [ ] Try by voice once voice exists: "remember I prefer…"

## 5. Scheduled & triggered actions  — *Priority 5*

Ultron can now start things itself: `backend/scheduler.py` runs jobs from `storage/jobs.json`.

- [x] Scheduler inside the backend (asyncio loop, checks every 30 s) that survives restarts (jobs saved in `storage/jobs.json`; a job missed while the Mac slept still runs if it's under 3 hours late)
- [ ] **Scheduled jobs** (time of day + days) — the mechanism works (tested live with a test job); each of these is one sentence to Ultron, the prompt has the recipe. Not set up or tried yet:
  - [ ] Morning briefing: today's calendar, due reminders, important unread email, weather ("give me a briefing every weekday at 8")
  - [ ] Evening wrap-up: what's left, what's tomorrow
  - [ ] Weekly review (Sunday): upcoming week, overdue tasks
- [ ] **Triggered jobs** (watchers: check every N minutes, at least 15, only speak up when there's news) — mechanism tested with fakes only, no live watcher yet:
  - [ ] "Tell me when X replies" → checks Gmail, stops after it has told you
  - [ ] "Tell me 15 min before meetings" → calendar watcher (a 15-minute check can't hit "15 min before" exactly)
  - [ ] "Tell me if the price of X drops" → web check
- [x] Create / list / pause / delete jobs by chat ("what have you got scheduled?"): `schedule_job`, `change_job` (act, no card), `list_jobs`; also the clock button in the top bar (run now, pause, delete)
- [x] Jobs only run **read** tools on their own; an **act** tool is refused and the job tells you what it suggests instead
- [ ] Queue a refused act so you can approve it later from the notification (today you ask Ultron to do it when you're back)
- [x] Rate/usage guard: jobs are skipped above 80% of the 5-hour limit (`JARVIS_JOBS_MAX_USAGE`), at most 10 jobs, one at a time, watchers on Haiku and paused in quiet hours
- [x] Log of past runs (what ran, when, result): the last 100, in the clock panel and `list_jobs`

## 6. Notifications  — *Priority 5 (ships with the scheduler)*

The channel proactive actions need to reach you when the chat isn't open. `backend/notify.py`: every job result goes to the open chat, a macOS notification and your phone (Telegram).

- [x] macOS notifications (`osascript display notification`, tested live)
- [ ] Clicking a notification opens Ultron on the related card (needs `terminal-notifier`; osascript notifications open Script Editor)
- [x] Phone text → `text_me`: Ultron's own Telegram bot, only ever to your chat (fixed in `.env`), no confirm
- [x] Job results are texted to the phone too, when Telegram is set up
- [ ] Telegram: first live text, by the user (from Claude's test run Python couldn't verify Telegram's certificate; check it works when you run Ultron yourself)
- [ ] Reply to Ultron from the phone (long-poll `getUpdates` into a chat; no open port needed)
- [ ] Phone calls (needs voice): Twilio number; one-way spoken call first, live conversation needs a public tunnel
- [ ] Spoken alert via TTS when Ultron is open (`backend/voice/tts.py`; needs voice, Phase 5)
- [x] Quiet hours: watchers don't run 23:00–07:00 (`JARVIS_QUIET_HOURS`); a job you set for a time of day still runs
- [x] Notification history in the UI (clock button → recent runs); Ultron also gets what the jobs told you with your next message, so "reply to that" works

## 7. macOS integration  — *Priority 6*

`backend/tools/mac.py`: `mac_read` (read), `mac_change` and `run_python` (act, no card; jobs can't use them). Unit-tested; the changes (open, copy, volume, dark mode, trash) not tried live yet.

- [x] Run existing Shortcuts (`shortcuts run "<name>"`, with text input/output), list available Shortcuts (you have none yet)
- [x] Open / focus apps (only from the Applications folders), open URLs (http/https only) and files (documents only, so nothing in the folder can run as a program; folders show in Finder)
- [x] Read clipboard (`pbpaste`), write clipboard (`pbcopy`)
- [x] Sandboxed file access: one folder (`JARVIS_FILES_DIR`, default `~/Jarvis Files`; `~/Ultron` was taken by another project), find / move / rename / organize files
- [x] Code-execution sandbox for data work: Python stdlib in `sandbox-exec` (no network, no other programs or Apple Events, reads only the folder, writes only `Output/`, 60 s). No pandas: add a separate venv if stdlib gets painful
- [x] System info: battery, volume, dark mode, Wi-Fi (read; macOS hides the Wi-Fi name without Location permission); volume/mute/dark mode changes. Do Not Disturb: through a Shortcut you make ("Set Focus")
- [x] Location: `scripts/setup_location.sh` builds `UltronLocation.app` (Swift, CoreLocation; macOS only gives Location to an app), allowed 2026-10-01. `mac_read what=location` → coordinates, place name, time zone (tested live). Ready for weather, "near me" and item 8's travel times
- [x] Destructive actions: delete = Trash (recoverable), moving out of the folder and overwriting are refused outright. No card, per the approval rule (only other people / important files ask); files marked important still ask
- [ ] Try live: "open Calculator", "copy this", "set volume to 30", "move X into Y", "trash X", a CSV analysis (first dark mode / trash makes macOS ask for Automation permission)

## 8. Messaging + maps/travel  — *Priority 7*

Most personal communication isn't email, and "when should I leave?" needs live traffic.

- [ ] **Messaging**
  - [-] iMessage send / read: skipped, you don't use iMessage
  - [ ] Slack (connector) read/send
  - [x] WhatsApp send → `whatsapp_send`: after the confirm card, opens the chat via `whatsapp://send` in WhatsApp desktop and presses Enter (only if WhatsApp is in front). Needs Accessibility permission. No reading (unofficial libraries risk a ban)
  - [ ] WhatsApp: first live send, by the user
- [x] **Maps / travel** → `maps` tool (read): Apple MapKit through `UltronLocation.app` (`scripts/locate.swift`), no API key. Chosen over the TomTom connector (needs a TomTom account)
  - [x] Directions + travel time with live traffic: driving / walking / transit, distance, depart/arrive times, Apple Maps link (tested live in Dubai)
  - [x] "When should I leave for my 3pm?" = calendar location + `arrive_by` (prompt recipe; maps part tested live, the whole flow not tried in chat yet)
  - [x] Nearby places search ("coffee near me"), nearest first, also "near <place>" (tested live)
  - [x] Add travel time as a buffer to calendar events: a "Travel to X" event, when asked; offered once for events with a location (prompt)
  - [ ] Try in chat: "when should I leave for my next meeting", "block travel time for it", "pharmacy near me"
  - [x] Map on the canvas: `show_on_canvas` kind `map` = Google Maps' embed (no key), a place or a route, map or satellite view, pan/zoom, "Open in Google Maps" link (tested live: satellite route to Dubai Mall)
  - [ ] Turn-by-turn steps aren't returned (just time, distance, link); add if wanted

---

## Honorable mentions (later)

- [ ] **HomeKit / smart home** — lights, thermostat, scenes (via Shortcuts is the easy path)
- [ ] **Password manager** — read-only, strict confirm every time, never shown in chat
- [ ] **Finance / receipt tracking** — parse receipt emails, monthly spend summary
- [ ] **Google Drive / iCloud documents** — search and read docs, attach to emails
- [x] **YouTube search** — `youtube` tool (read): YouTube's search page via curl, no key, up to 20 videos with channel/length/views/age/link; shown on the canvas as a `youtube` card: YouTube's player plus the other results with thumbnails, click to play (tested live in chat: "find me rocket league videos")
  - [ ] Not signed in, so no subscriptions, history or Watch Later; add via Chrome if wanted

## Milestone: Daily briefing

Done when all of these work together:
- [ ] Every weekday at a set time, Ultron sends a notification (possible now: ask for the briefing job)
- [ ] Opening it shows: today's events, due/overdue reminders, important emails, weather, leave-by times (leave-by now possible: the prompt asks for it in briefings)
- [ ] Follow-ups by voice: "move my 2pm", "remind me to reply to that tonight", "remember I prefer…"
