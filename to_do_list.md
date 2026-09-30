# Jarvis To-Do List

**Main gap:** Jarvis is already strong at *creating* things (images, 3D, video, apps) and at email.
It's weak at the core of personal assistance: **time, memory, people, and acting on its own.**

**Build order:** Calendar → Reminders → Memory → Scheduler + Notifications.
Together these four enable a **daily briefing with follow-ups**, the thing that makes Jarvis feel like a real assistant.

**Ground rules for every item**
- Reads run freely; writes/sends/deletes go through the existing confirm gate (`backend/brain/confirm.py`, `tools/connectors.py` read/act labels).
- Prefer a claude.ai connector when one exists; only write a local tool (`backend/tools/`) when there isn't one.
- Every new tool gets one small test in `backend/tests/`.
- Show lists (events, tasks, contacts) on canvas cards, keep the chat reply short.

---

## 1. Calendar read/write  — *Priority 1*

Today: events can be displayed on the canvas, but Jarvis can't create, move, or check availability.

- [x] Confirm which calendar Jarvis uses → **Google Calendar connector** (claude.ai). Enable it at claude.ai → Settings → Connectors.
- [ ] **Read**
  - [ ] "What's on my calendar today / tomorrow / this week" → event cards on the canvas
  - [ ] Free/busy lookup: "Am I free Thursday at 3?" / "Find me a free hour tomorrow afternoon"
  - [ ] Handle time zones and all-day events correctly
- [ ] **Write** (all through the confirm card)
  - [x] Create event: title, start/end, location, attendees, notes, video link
  - [x] Move / reschedule an event ("push my 3pm to 4")
  - [x] Cancel / delete an event (card shows the event's title + time, from events Jarvis has seen)
  - [ ] Invite attendees → needs Contacts (item 3) to resolve names
- [ ] Confirm card for events shows: title, date/time, duration, attendees, calendar name (title + times work; no duration or calendar name row yet)
- [x] Natural-language dates (each message now starts with a `[Now: …]` note): "next Friday", "in two weeks", "the day after my dentist appointment"
- [x] Conflict warning when a new event overlaps an existing one (prompt)
- [x] Update `brain/prompts.py` so Jarvis knows it can write, not just read
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
- [ ] Remember aliases in Memory (item 4): "Sarah" = Sarah K. from work
- [ ] Wire into email (to/cc), calendar invites, and messaging (item 8) (prompt: look up before emailing/inviting; needs a test by you, since it sends)
- [x] Read-only by default (no add/edit tool at all; add one with an "act" label if ever needed)

## 4. Persistent user memory  — *Priority 4* (README Phase 6, `backend/tools/memory.py` is still a stub)

Goal: Jarvis *knows you* between chats. A store you can inspect and edit, not raw chat history.

- [ ] Storage: one file or SQLite table in `backend/storage/` (id, category, text, source, created, updated)
- [ ] Categories: **preferences**, **people**, **projects**, **decisions**, **facts about me**
- [ ] Tools: `remember(text, category)`, `recall(query)`, `forget(id)` — `remember`/`forget` go through confirm or at least show a "Saved to memory" toast
- [ ] Load a short summary of relevant memories into the system prompt at chat start (keep it small — token budget)
- [ ] Jarvis proposes memories itself ("Should I remember you prefer morning meetings?") instead of saving silently
- [ ] **Memory panel** in the UI: list, search, edit, delete entries
- [ ] Never store secrets (passwords, card numbers, tokens) — filter before saving
- [ ] Export / wipe all memory button
- [ ] Test: remember → new chat → recall

## 5. Scheduled & triggered actions  — *Priority 5*

Today: Jarvis only responds, never initiates.

- [ ] Scheduler inside the backend (asyncio loop or APScheduler) that survives restarts (jobs saved in `storage/`)
- [ ] **Scheduled jobs** (cron-style)
  - [ ] Morning briefing: today's calendar, due reminders, important unread email, weather
  - [ ] Evening wrap-up: what's left, what's tomorrow
  - [ ] Weekly review (Sunday): upcoming week, overdue tasks
- [ ] **Triggered jobs** (watchers)
  - [ ] "Tell me when X replies" → poll Gmail for a thread reply
  - [ ] "Tell me 15 min before meetings" → calendar watcher
  - [ ] "Tell me if the price of X drops" → web check
- [ ] Create / list / pause / delete jobs by voice or chat ("what have you got scheduled?")
- [ ] Jobs only run **read** tools on their own; any **act** tool waits for you (queue it, notify, confirm later)
- [ ] Rate/usage guard so background jobs don't burn the Pro usage limit
- [ ] Log of past runs (what ran, when, result)

## 6. Notifications  — *Priority 5 (ships with the scheduler)*

The channel proactive actions need to reach you when the chat isn't open.

- [ ] macOS notifications (`osascript -e 'display notification ...'` or `terminal-notifier`)
- [ ] Clicking a notification opens Jarvis on the related card
- [ ] Phone push (later): ntfy.sh / Pushover / Telegram bot
- [ ] Spoken alert via TTS when Jarvis is open (`backend/voice/tts.py`)
- [ ] Quiet hours / do-not-disturb setting
- [ ] Notification history in the UI

## 7. macOS integration  — *Priority 6*

- [ ] Run existing Shortcuts (`shortcuts run "<name>"`), list available Shortcuts
- [ ] Open / focus apps, open URLs and files
- [ ] Read clipboard (`pbpaste`), write clipboard (`pbcopy`)
- [ ] Sandboxed file access: one allowed folder (e.g. `~/Jarvis`), find / move / rename / organize files
- [ ] Code-execution sandbox for data work (CSV analysis, quick scripts)
- [ ] System info: battery, volume, dark mode, Wi-Fi (read); volume/do-not-disturb changes need confirm
- [ ] **Always confirm** destructive actions (delete, overwrite, move out of the sandbox)

## 8. Messaging + maps/travel  — *Priority 7*

Most personal communication isn't email, and "when should I leave?" needs live traffic.

- [ ] **Messaging**
  - [ ] iMessage send (AppleScript via Messages.app) — always confirm
  - [ ] iMessage read recent (needs Full Disk Access to `chat.db`, read-only)
  - [ ] Slack (connector) read/send
  - [x] WhatsApp send → `whatsapp_send`: after the confirm card, opens the chat via `whatsapp://send` in WhatsApp desktop and presses Enter (only if WhatsApp is in front). Needs Accessibility permission. No reading (unofficial libraries risk a ban)
  - [ ] WhatsApp: first live send, by the user
- [ ] **Maps / travel**
  - [ ] Directions + travel time with live traffic (Google Maps / Apple Maps API)
  - [ ] "When should I leave for my 3pm?" = calendar location + travel time
  - [ ] Nearby places search ("coffee near me")
  - [ ] Add travel time as a buffer to calendar events

---

## Honorable mentions (later)

- [ ] **HomeKit / smart home** — lights, thermostat, scenes (via Shortcuts is the easy path)
- [ ] **Password manager** — read-only, strict confirm every time, never shown in chat
- [ ] **Finance / receipt tracking** — parse receipt emails, monthly spend summary
- [ ] **Google Drive / iCloud documents** — search and read docs, attach to emails

## Milestone: Daily briefing

Done when all of these work together:
- [ ] Every weekday at a set time, Jarvis sends a notification
- [ ] Opening it shows: today's events, due/overdue reminders, important emails, weather, leave-by times
- [ ] Follow-ups by voice: "move my 2pm", "remind me to reply to that tonight", "remember I prefer…"
