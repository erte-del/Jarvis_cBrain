# Graph Report - Jarvis_cBrain  (2026-09-28)

## Corpus Check
- Corpus is ~29,041 words - fits in a single context window. You may not need a graph.

## Summary
- 752 nodes · 1416 edges · 44 communities (32 shown, 12 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 66 edges (avg confidence: 0.9)
- Token cost: 150,630 input · 0 output

## Community Hubs (Navigation)
- Asset API & Model Store
- React UI Components
- 3D Shape Geometry Builder
- Image Editing Tests
- Image Version Store
- Storage & 3D Model Tests
- Frontend npm Dependencies
- Confirmation Gate
- Web Helper Tests
- Brain Protocol Events
- WebSocket Hub & API Brain
- Registry & Router Tests
- Expert Canvas Tests
- TS App Config
- Jarvis Agent Core
- UI Event Builders
- TS Node Config
- FastAPI App & Config
- Blender Scripts & Icon
- Model Router & Connectors
- Claude Code Session Startup
- Planned Tools & Memory
- 3D Export Design Docs
- Project Readme & Deps
- Brain Architecture Docs
- WebSocket Turn Handler
- API Brain Placeholder
- Connectors & Usage Settings
- Oxlint Config
- Idle Reset Handling
- Architecture & Dev Run
- Read/Act Tool Labels
- Favicon Orb
- TS Root Config
- Start Script
- SQLite DB Stub
- Memory Stub
- Voice Package Stub
- Speech-to-Text Stub
- Text-to-Speech Stub
- VAD Stub
- App Bundle Script
- Stop Script

## God Nodes (most connected - your core abstractions)
1. `ClaudeCodeBrain` - 19 edges
2. `compilerOptions` - 18 edges
3. `EditError` - 17 edges
4. `compilerOptions` - 15 edges
5. `Done` - 14 edges
6. `ImageRecord` - 14 edges
7. `ModelRecord` - 14 edges
8. `Jarvis` - 13 edges
9. `from_brain()` - 13 edges
10. `StoreTest` - 12 edges

## Surprising Connections (you probably didn't know these)
- `Never Add ANTHROPIC_API_KEY` --semantically_similar_to--> `Claude Pro Subscription via Claude Code`  [INFERRED] [semantically similar]
  README.md → JARVIS_BUILD_PROMPT.md
- `claude-agent-sdk==0.2.160` --semantically_similar_to--> `Claude Agent SDK (claude-agent-sdk)`  [INFERRED] [semantically similar]
  backend/requirements.txt → JARVIS_BUILD_PROMPT.md
- `tools/shapes.py Geometry Builder (trimesh)` --references--> `trimesh + geometry deps (numpy, shapely, mapbox-earcut, scipy, rtree)`  [INFERRED]
  JARVIS_BUILD_PROMPT.md → backend/requirements.txt
- `Jarvis_cBrain README` --references--> `Jarvis Personal AI Assistant`  [EXTRACTED]
  README.md → JARVIS_BUILD_PROMPT.md
- `Jarvis_cBrain README` --references--> `Claude Pro Subscription via Claude Code`  [INFERRED]
  README.md → JARVIS_BUILD_PROMPT.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Act tools gated by confirmation** — jarvis_build_prompt_confirmation_gate, jarvis_build_prompt_export_3d, jarvis_build_prompt_connectors, jarvis_build_prompt_read_act_labels [EXTRACTED 1.00]
- **3D spec to preview to Blender export flow** — jarvis_build_prompt_scene_spec, jarvis_build_prompt_shapes_builder, jarvis_build_prompt_three_js_viewer, jarvis_build_prompt_preview_3d, jarvis_build_prompt_export_3d, jarvis_build_prompt_blender_export [EXTRACTED 1.00]
- **Pro usage-limit conservation strategies** — jarvis_build_prompt_model_router, jarvis_build_prompt_sticky_routing, jarvis_build_prompt_new_chat_idle_reset, jarvis_build_prompt_usage_settings, jarvis_build_prompt_ask_expert [INFERRED 0.85]

## Communities (44 total, 12 thin omitted)

### Community 0 - "Asset API & Model Store"
Cohesion: 0.06
Nodes (64): asset(), health(), model_file(), Image files for the canvas. Names are checked strictly, so only stored images…, 3D previews (.glb) and finished exports. Names are checked strictly., add_export(), add_version(), card_data() (+56 more)

### Community 1 - "React UI Components"
Cohesion: 0.06
Nodes (57): App(), CONNECTION_LABEL, Canvas(), CanvasProps, CardBody(), EmailList(), Events(), isUnread() (+49 more)

### Community 2 - "3D Shape Geometry Builder"
Cohesion: 0.08
Nodes (49): _build_preview(), apply_changes(), build_scene(), _display_name(), floating_parts(), _gap(), _linear(), _loft() (+41 more)

### Community 3 - "Image Editing Tests"
Cohesion: 0.10
Nodes (33): OpsTest, Image, Image editing and storage tests (no network). Run from the backend folder:…, sample(), StoreTest, add_border(), add_text(), apply_all() (+25 more)

### Community 4 - "Image Version Store"
Cohesion: 0.12
Nodes (38): add_version(), card_data(), create(), _dir(), file_path(), ImageRecord, load(), open_version() (+30 more)

### Community 5 - "Storage & 3D Model Tests"
Cohesion: 0.07
Nodes (9): Local storage: SQLite + assets/ folder., FloatingTest, NewShapesTest, 3D preview and export tests. Run from the backend folder: .venv/bin/python -m…, ShapesTest, SmallChangesTest, StoreTest, skipUnless (+1 more)

### Community 6 - "Frontend npm Dependencies"
Cohesion: 0.06
Nodes (34): dependencies, react, react-dom, react-markdown, remark-gfm, three, devDependencies, oxlint (+26 more)

### Community 7 - "Confirmation Gate"
Cohesion: 0.09
Nodes (16): asyncio, ConfirmationGate, _Pending, Any, Event, Confirmation gate for 'act' tools. (Phase 4a) Claude Code runs 'read' tools…, Called by Claude Code before any tool that isn't auto-allowed., Record your answer from the browser. False if nothing was waiting. (+8 more)

### Community 8 - "Web Helper Tests"
Cohesion: 0.10
Nodes (22): PublicUrlTest, Web helper tests. Run from the backend folder: .venv/bin/python -m unittest…, SourcesTest, block_private_urls(), domain(), _is_public_ip(), is_public_url(), links_in_text() (+14 more)

### Community 9 - "Brain Protocol Events"
Cohesion: 0.15
Nodes (19): Done, Error, Brain protocol + BrainEvent types. Everything in Jarvis talks to a `Brain`,…, A small piece of the reply text, streamed as it is generated., Claude started using a tool (e.g. a web search)., A tool finished. `data` is the tool's structured result, when there is one., The reply is complete. `model` is the full model ID that answered., TextDelta (+11 more)

### Community 10 - "WebSocket Hub & API Brain"
Cohesion: 0.11
Nodes (23): Placeholder: API-key brain. Not used. Jarvis runs on the Claude Pro…, connect(), disconnect(), emit(), has_clients(), Event, Sender, Pushes events to every open browser tab. Replies stream back on the tab that… (+15 more)

### Community 11 - "Registry & Router Tests"
Cohesion: 0.13
Nodes (5): ClassifyTest, Read/act labels. Run from the backend folder: .venv/bin/python -m unittest…, Router tests. Run from the backend folder: .venv/bin/python -m unittest…, RouterTest, unittest

### Community 12 - "Expert Canvas Tests"
Cohesion: 0.14
Nodes (4): ExpertCanvasTest, FakeBrain, IdleStartOverTest, tab()

### Community 13 - "TS App Config"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 14 - "Jarvis Agent Core"
Cohesion: 0.13
Nodes (12): Jarvis, Jarvis logic: router -> brain -> events., Brain, BrainEvent, Send one user message and stream back events until `Done` or `Error`., Forget the conversation and start a fresh one., Release resources (e.g. stop the Claude Code process)., Usage-saving behaviour: starting over after a long break, expert answers on the… (+4 more)

### Community 15 - "UI Event Builders"
Cohesion: 0.17
Nodes (17): Something for the frontend to show (canvas image, card, ...). Phase 4a+., UIEvent, The model the conversation is on now., canvas_card(), confirm_request(), confirm_resolved(), conversation_new(), done() (+9 more)

### Community 16 - "TS Node Config"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 17 - "FastAPI App & Config"
Cohesion: 0.15
Nodes (14): Settings loaded from .env., Remove API credentials from this process so Claude Code falls back to the Pro…, use_pro_login(), lifespan(), FastAPI app + /ws WebSocket, bound to 127.0.0.1. Run from the backend folder:…, contextlib, dotenv, FastAPI (+6 more)

### Community 18 - "Blender Scripts & Icon"
Cohesion: 0.17
Nodes (13): Runs INSIDE Blender (never imported by Jarvis). Fixed script: Claude never…, Runs INSIDE Blender (never imported by Jarvis). Fixed script: Claude never…, bpy, math, mathutils, pathlib, pil, draw() (+5 more)

### Community 19 - "Model Router & Connectors"
Cohesion: 0.18
Nodes (10): Haiku / Sonnet / Opus selection. Order of checks: 1. The model picked in the UI…, Route, is_read(), parse(), claude.ai connectors (Gmail, Supabase, Canva, ...): read/act labels. Claude…, mcp__claude_ai_Gmail__search_threads' -> ('Gmail', 'search_threads'). None if…, classify(), read' (runs freely) or 'act' (asks you first) for any tool name Claude Code… (+2 more)

### Community 20 - "Claude Code Session Startup"
Cohesion: 0.24
Nodes (5): Give slow connectors a moment, so the first message can already use them., Switch claude.ai connectors on or off to match JARVIS_CONNECTORS (.env). Claude…, Start Claude Code ahead of the first message (called at server startup)., ClaudeAgentOptions, ClaudeSDKClient

### Community 21 - "Planned Tools & Memory"
Cohesion: 0.22
Nodes (10): pillow, ask_expert Tool (Sonnet delegates to Opus), Canvas (images and cards UI), image_edit Tool (Pillow, versioned), image_search Tool (Pexels/Unsplash), Jarvis System Prompt, Memory (SQLite history, remember/recall/forget), Model Router (router.py: Haiku/Sonnet/Opus) (+2 more)

### Community 22 - "3D Export Design Docs"
Cohesion: 0.20
Nodes (10): Blender Final Export (blender_export_script.py), Build Phases 1-7, export_3d Tool (act), Claude Never Writes Code That Runs Locally, 3D Objects Preview Mode (Phase 4d), Scene Spec (JSON list of parts), tools/shapes.py Geometry Builder (trimesh), three.js GLB Preview Viewer (+2 more)

### Community 23 - "Project Readme & Deps"
Cohesion: 0.28
Nodes (9): claude-agent-sdk==0.2.160, Backend Python Requirements, trimesh + geometry deps (numpy, shapely, mapbox-earcut, scipy, rtree), Claude Agent SDK (claude-agent-sdk), Jarvis Personal AI Assistant, Claude Pro Subscription via Claude Code, Jarvis.app (scripts/make_app.sh), Jarvis_cBrain README (+1 more)

### Community 24 - "Brain Architecture Docs"
Cohesion: 0.25
Nodes (9): API-Key Brain Placeholder (brain_api.py), brain_claudecode.py (Agent SDK brain), Brain Protocol (swappable brain interface), BrainEvent (text_delta/tool_start/tool_result/ui_event/done/error), Confirmation Gate (confirm.py), Persistent ClaudeSDKClient Session, Voice Pipeline (VAD, faster-whisper STT, Piper TTS), Web Search (built-in WebSearch/WebFetch) (+1 more)

### Community 25 - "WebSocket Turn Handler"
Cohesion: 0.39
Nodes (8): make_sender(), send(), Sender, Answer one user message and stream the reply to the browser., Send JSON to one tab. The lock stops a reply and a hub event (e.g. a…, run_turn(), websocket_endpoint(), WebSocket

### Community 27 - "Connectors & Usage Settings"
Cohesion: 0.33
Nodes (6): Connector MCP Configs (fallback), No __init__.py in backend/mcp, Claude Connectors (Gmail, Calendar, Drive), MCP Server Fallback (backend/mcp/), New Chat / Idle Reset, Usage Settings (JARVIS_EFFORT, JARVIS_CONNECTORS, JARVIS_NEW_CHAT_AFTER_IDLE_MIN)

### Community 28 - "Oxlint Config"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 29 - "Idle Reset Handling"
Cohesion: 0.40
Nodes (3): Event, A big conversation left alone for over an hour: Claude's cached copy has…, Answer one user message, yielding WebSocket events for the browser.

### Community 30 - "Architecture & Dev Run"
Cohesion: 0.40
Nodes (5): fastapi / uvicorn, Jarvis Frontend index.html (Vite entry, #root, /src/main.tsx), Jarvis Architecture (React frontend + FastAPI backend over WebSocket), Bind Backend to 127.0.0.1 Only, Dev Run (backend :8000, Vite :5173, chat_cli.py)

### Community 31 - "Read/Act Tool Labels"
Cohesion: 0.50
Nodes (4): preview_3d Tool (read), Read / Act Tool Labels, Blender 4-View Self-Check Render, Tool Registry (tools/registry.py, SDK MCP server)

### Community 32 - "Favicon Orb"
Cohesion: 0.67
Nodes (3): AI Core Orb Visual Identity, Favicon (glowing cyan orb), Radial Gradient g (cyan-to-teal)

## Knowledge Gaps
- **89 isolated node(s):** `$schema`, `plugins`, `react/rules-of-hooks`, `react/only-export-components`, `name` (+84 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 289 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **12 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ClaudeCodeBrain` connect `Brain Protocol Events` to `FastAPI App & Config`, `Claude Code Session Startup`, `UI Event Builders`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Why does `ConfirmationGate` connect `Confirmation Gate` to `FastAPI App & Config`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `ClaudeCodeBrain` (e.g. with `Done` and `Error`) actually correct?**
  _`ClaudeCodeBrain` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `EditError` (e.g. with `OpsTest` and `image_edit()`) actually correct?**
  _`EditError` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugins`, `react/rules-of-hooks` to the rest of the system?**
  _89 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Asset API & Model Store` be split into smaller, more focused modules?**
  _Cohesion score 0.05955734406438632 - nodes in this community are weakly interconnected._
- **Should `React UI Components` be split into smaller, more focused modules?**
  _Cohesion score 0.0579476861167002 - nodes in this community are weakly interconnected._