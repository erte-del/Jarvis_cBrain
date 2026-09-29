// WebSocket client + event handling. Mirrors backend/events.py.

import { useCallback, useEffect, useReducer, useRef } from 'react'

export const API_BASE = 'http://127.0.0.1:8000'
const WS_URL = 'ws://127.0.0.1:8000/ws'

export type ModelAlias = 'haiku' | 'sonnet' | 'opus'
export type Provider = 'claude' | 'omniroute'

export interface BrainSettings {
  provider: Provider
  gateway_url: string
  gateway_model: string // the OmniRoute model in use, e.g. "groq/openai/gpt-oss-120b"
  gateway_models: string[] // the ones you can switch between (JARVIS_GATEWAY_MODELS)
}

export interface UsageWindow {
  used: number // 0..1 of the plan window
  resets_at: number // unix seconds, 0 = not reported yet
  reported_at: number // unix seconds: when Claude Code last told us (with a Jarvis reply)
}

export interface UsageSnapshot {
  provider: Provider
  windows: Record<string, UsageWindow> // five_hour, seven_day, ...
  tokens: { input: number; cache_write: number; cache_read: number; output: number } // Jarvis, this 5h window
  context_tokens: number // size of the current conversation
}

export interface SavedChat {
  id: string
  title: string // the first thing you said
  provider: Provider
  saved_at: number // unix seconds
}

export interface LogLine {
  id: number
  time: string // HH:MM:SS
  text: string
  tone?: 'ok' | 'warn' | 'error'
}

// Server -> browser
export type ServerEvent =
  | { type: 'status'; state: 'idle' | 'thinking' }
  | { type: 'assistant.text_delta'; id: string; text: string }
  | {
      type: 'assistant.done'
      id: string
      model: string // full model ID that answered
      routed_to: ModelAlias // the router's pick
      reason: string // why the router picked it
      expert: boolean // Opus was consulted via ask_expert
      sources: Source[] // web pages behind the answer
    }
  | { type: 'tool.started'; id: string; name: string; detail: string; label: string }
  | { type: 'tool.finished'; id: string; is_error: boolean }
  | { type: 'error'; message: string; id?: string }
  | { type: 'notice'; message: string }
  | { type: 'confirm.request'; id: string; title: string; summary: string; details: [string, string][] }
  | { type: 'confirm.resolved'; id: string; status: ConfirmStatus }
  | { type: 'canvas.card'; id: string; kind: string; title: string; data: Record<string, unknown> }
  | { type: 'conversation.new'; reason: 'button' | 'idle' | 'provider' }
  | { type: 'conversation.loaded'; messages: Pick<ChatMessage, 'role' | 'text' | 'files' | 'model'>[]; cards: CanvasCard[] }
  | { type: 'chats.list'; chats: SavedChat[]; max: number }
  | ({ type: 'settings.state' } & BrainSettings)
  | ({ type: 'usage.update' } & UsageSnapshot)

// Browser -> server
export type ClientEvent =
  | { type: 'user.text'; text: string; files?: string[] }
  | { type: 'user.confirm'; id: string; approved: boolean }
  | { type: 'user.select_image'; id: string | null; version?: number }
  | { type: 'settings.update'; model_override?: ModelAlias | null; provider?: Provider; gateway_model?: string }
  | { type: 'user.new_chat' }
  | { type: 'user.save_chat'; messages: ChatMessage[]; cards: CanvasCard[] }
  | { type: 'user.load_chat'; id: string }
  | { type: 'user.delete_chat'; id: string }

export type ConfirmStatus = 'pending' | 'approved' | 'denied' | 'expired'

export interface Confirmation {
  title: string
  summary: string
  details: [string, string][] // [label, value]
  status: ConfirmStatus
}

export interface ImageVersion {
  version: number
  note: string
  url: string // relative to API_BASE
  thumb_url: string
  width: number
  height: number
}

export interface ImageCardData {
  image_id: string
  current: number
  credit: { photographer?: string; photographer_url?: string; source_url?: string; source?: string }
  versions: ImageVersion[]
}

export interface Model3DData {
  model_id: string
  current: number
  versions: { version: number; note: string; parts: number; size: [number, number, number]; preview_url: string }[]
  exports: { version: number; format: string; url: string; name: string }[]
}

export interface VideoCardData {
  video_id: string
  prompt: string
  status: 'rendering' | 'done' | 'failed'
  progress: number // 0–1
  error: string
  seconds: number
  width: number
  height: number
  url: string // relative to API_BASE; empty until done
  download_name: string
}

export interface ImageSelection {
  id: string
  version: number
}

export interface CanvasCard {
  id: string
  kind: string // 'text' | 'table' for now; more kinds in later steps
  title: string
  data: Record<string, unknown>
}

export type ConnectionState = 'connecting' | 'open' | 'closed'

export interface Source {
  title: string
  url: string
}

export interface ActiveTool {
  name: string
  detail: string // e.g. the search query or the site being read
  label: string // readable name, e.g. "Gmail: Search threads"
}

export interface Attachment {
  id: string // upl_003, or img_007 for an image (it goes on the canvas)
  name: string
}

/** Send a file from your computer to the backend; attach the result to the next message. */
export async function uploadFile(file: File): Promise<Attachment> {
  const res = await fetch(`${API_BASE}/upload?name=${encodeURIComponent(file.name)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/octet-stream' },
    body: file,
  })
  if (!res.ok) throw new Error((await res.json().catch(() => null))?.detail ?? `Upload failed (${res.status})`)
  return res.json()
}

// ---------------------------------------------------------------------------
// Socket: one connection that reconnects by itself if the backend restarts.

export class JarvisSocket {
  private ws: WebSocket | null = null
  private retryMs = 500
  private retryTimer: number | undefined
  private stopped = false

  onEvent: (ev: ServerEvent) => void = () => {}
  onConnection: (state: ConnectionState) => void = () => {}
  onOpen: () => void = () => {}

  connect() {
    this.stopped = false
    this.onConnection('connecting')
    const ws = new WebSocket(WS_URL)
    this.ws = ws

    ws.onopen = () => {
      this.retryMs = 500
      this.onConnection('open')
      this.onOpen()
    }
    ws.onmessage = (msg) => {
      try {
        this.onEvent(JSON.parse(msg.data) as ServerEvent)
      } catch {
        console.warn('Bad message from server', msg.data)
      }
    }
    ws.onclose = () => {
      if (this.ws !== ws) return
      this.ws = null
      this.onConnection('closed')
      if (!this.stopped) {
        this.retryTimer = window.setTimeout(() => this.connect(), this.retryMs)
        this.retryMs = Math.min(this.retryMs * 2, 5000)
      }
    }
  }

  send(ev: ClientEvent): boolean {
    if (this.ws?.readyState !== WebSocket.OPEN) return false
    this.ws.send(JSON.stringify(ev))
    return true
  }

  close() {
    this.stopped = true
    window.clearTimeout(this.retryTimer)
    this.ws?.close()
    this.ws = null
  }
}

// ---------------------------------------------------------------------------
// Chat state: turns the event stream into a list of messages.

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'notice' | 'confirm'
  text: string
  info?: boolean // role 'notice': just so you know, not an error
  confirm?: Confirmation // role 'confirm': an action waiting for your approval
  model?: string // full model ID that answered (assistant only)
  reason?: string // why the router picked the model
  expert?: boolean // Opus was consulted via ask_expert
  sources?: Source[]
  files?: string[] // role 'user': names of attached files
  done?: boolean
  error?: string
}

interface ChatState {
  messages: ChatMessage[]
  connection: ConnectionState
  busy: boolean // a reply is in progress
  activeTool: ActiveTool | null
  modelOverride: ModelAlias | null
  cards: CanvasCard[]
  stageTab: string // centre panel: 'core', 'cards', or the id of a 3D model
  selectedImage: ImageSelection | null
  settings: BrainSettings | null
  usage: UsageSnapshot | null
  savedChats: SavedChat[]
  maxSavedChats: number
  log: LogLine[]
}

type Action =
  | { kind: 'server'; ev: ServerEvent }
  | { kind: 'connection'; state: ConnectionState }
  | { kind: 'user'; text: string; files: Attachment[] }
  | { kind: 'override'; model: ModelAlias | null }
  | { kind: 'answer'; id: string; approved: boolean }
  | { kind: 'closeCard'; id: string }
  | { kind: 'select'; selection: ImageSelection | null }
  | { kind: 'tab'; tab: string }

let localId = 0
const nextLocalId = () => `local-${++localId}`

function updateMessage(
  messages: ChatMessage[],
  id: string,
  change: (m: ChatMessage) => ChatMessage,
): ChatMessage[] {
  const i = messages.findIndex((m) => m.id === id)
  if (i === -1) {
    return [...messages, change({ id, role: 'assistant', text: '' })]
  }
  const copy = messages.slice()
  copy[i] = change(copy[i])
  return copy
}

// ---------------------------------------------------------------------------
// System log (right-hand panel): one line per thing that happened.

const MAX_LOG = 80
let logId = 0

const clock = () => new Date().toLocaleTimeString([], { hour12: false })
const clip = (s: string, n = 48) => (s.length > n ? s.slice(0, n - 1) + '…' : s)
const family = (model: string) => (/haiku|sonnet|opus/i.exec(model)?.[0] ?? model).toUpperCase()

function logLine(state: ChatState, action: Action): Omit<LogLine, 'id' | 'time'> | null {
  switch (action.kind) {
    case 'user':
      return { text: `INPUT RECEIVED › "${clip(action.text)}"` }
    case 'connection':
      if (action.state === 'open') return { text: 'LINK ESTABLISHED · BACKEND ONLINE', tone: 'ok' }
      if (action.state === 'closed' && state.connection === 'open') return { text: 'LINK LOST · BACKEND OFFLINE', tone: 'error' }
      return null
    case 'server': {
      const ev = action.ev
      switch (ev.type) {
        case 'tool.started':
          return { text: `${ev.label.toUpperCase()}${ev.detail ? ` › ${clip(ev.detail, 36)}` : ''}` }
        case 'assistant.done':
          return { text: `RESPONSE COMPLETE · ${family(ev.model)}${ev.expert ? ' + OPUS' : ''}`, tone: 'ok' }
        case 'confirm.request':
          return { text: `AWAITING APPROVAL · ${ev.title.toUpperCase()}`, tone: 'warn' }
        case 'confirm.resolved':
          return { text: `APPROVAL ${ev.status.toUpperCase()}`, tone: ev.status === 'approved' ? 'ok' : undefined }
        case 'canvas.card':
          return { text: `CANVAS UPDATED · ${clip(ev.title, 36)}` }
        case 'conversation.new':
          return { text: `NEW CONVERSATION${ev.reason === 'idle' ? ' (IDLE OVER 1H)' : ''}`, tone: 'ok' }
        case 'conversation.loaded':
          return { text: 'SAVED CHAT LOADED', tone: 'ok' }
        case 'settings.state':
          if (state.settings?.provider !== ev.provider) {
            return { text: `BRAIN · ${ev.provider === 'claude' ? 'CLAUDE (PRO LOGIN)' : `OMNIROUTE (${ev.gateway_model})`}` }
          }
          if (ev.provider === 'omniroute' && state.settings?.gateway_model !== ev.gateway_model) {
            return { text: `MODEL · ${ev.gateway_model.toUpperCase()}` }
          }
          return null
        case 'error':
          return { text: `ERROR · ${clip(ev.message, 60)}`, tone: 'error' }
        case 'notice':
          return { text: ev.message.toUpperCase() }
      }
      return null
    }
  }
  return null
}

function reducer(state: ChatState, action: Action): ChatState {
  const next = baseReducer(state, action)
  const line = logLine(state, action)
  if (!line) return next
  return { ...next, log: [...next.log.slice(-(MAX_LOG - 1)), { ...line, id: ++logId, time: clock() }] }
}

function baseReducer(state: ChatState, action: Action): ChatState {
  switch (action.kind) {
    case 'user':
      return {
        ...state,
        busy: true,
        messages: [
          ...state.messages,
          { id: nextLocalId(), role: 'user', text: action.text, files: action.files.map((f) => f.name) },
        ],
      }

    case 'override':
      return { ...state, modelOverride: action.model }

    case 'answer':
      return {
        ...state,
        messages: updateMessage(state.messages, action.id, (m) =>
          m.confirm ? { ...m, confirm: { ...m.confirm, status: action.approved ? 'approved' : 'denied' } } : m,
        ),
      }

    case 'closeCard': {
      const cards = state.cards.filter((c) => c.id !== action.id)
      const selectedImage = state.selectedImage?.id === action.id ? null : state.selectedImage
      const hasCards = cards.some((c) => c.kind !== 'model3d')
      let stageTab = state.stageTab
      if (stageTab === action.id || (stageTab === 'cards' && !hasCards)) stageTab = hasCards ? 'cards' : 'core'
      return { ...state, cards, selectedImage, stageTab }
    }

    case 'tab':
      return { ...state, stageTab: action.tab }

    case 'select':
      return { ...state, selectedImage: action.selection }

    case 'connection': {
      if (action.state !== 'closed' || state.connection === 'closed') {
        return { ...state, connection: action.state }
      }
      // Lost the connection: any reply in progress won't finish.
      const messages = state.messages.map((m): ChatMessage => {
        if (m.role === 'assistant' && !m.done && !m.error) {
          return { ...m, error: 'Connection lost before the reply finished.' }
        }
        if (m.confirm?.status === 'pending') {
          return { ...m, confirm: { ...m.confirm, status: 'expired' } }
        }
        return m
      })
      return { ...state, connection: 'closed', busy: false, activeTool: null, messages }
    }

    case 'server': {
      const ev = action.ev
      switch (ev.type) {
        case 'status':
          return { ...state, busy: ev.state !== 'idle', activeTool: null }
        case 'assistant.text_delta':
          return {
            ...state,
            activeTool: null,
            messages: updateMessage(state.messages, ev.id, (m) => ({ ...m, text: m.text + ev.text })),
          }
        case 'assistant.done':
          return {
            ...state,
            messages: updateMessage(state.messages, ev.id, (m) => ({
              ...m,
              done: true,
              model: ev.model,
              reason: ev.reason,
              expert: ev.expert,
              sources: ev.sources,
            })),
          }
        case 'tool.started':
          return { ...state, activeTool: { name: ev.name, detail: ev.detail, label: ev.label } }
        case 'tool.finished':
          return { ...state, activeTool: null }
        case 'confirm.request': {
          const confirm: Confirmation = {
            title: ev.title,
            summary: ev.summary,
            details: ev.details,
            status: 'pending',
          }
          const exists = state.messages.some((m) => m.id === ev.id)
          return {
            ...state,
            messages: exists
              ? updateMessage(state.messages, ev.id, (m) => ({ ...m, confirm }))
              : [...state.messages, { id: ev.id, role: 'confirm', text: '', confirm }],
          }
        }
        case 'confirm.resolved':
          return {
            ...state,
            messages: updateMessage(state.messages, ev.id, (m) =>
              m.confirm ? { ...m, confirm: { ...m.confirm, status: ev.status } } : m,
            ),
          }
        case 'conversation.new': {
          if (ev.reason === 'button') return { ...state, messages: [] }
          // Started over by itself after a long break: say so above your new message.
          const notice: ChatMessage = {
            id: nextLocalId(),
            role: 'notice',
            text:
              'New conversation: the last one sat idle for over an hour, and sending it all to Claude ' +
              'again would use a lot of your limit. Jarvis no longer remembers the messages above.',
          }
          const lastUser = state.messages.map((m) => m.role).lastIndexOf('user')
          const messages = state.messages.slice()
          messages.splice(lastUser === -1 ? messages.length : lastUser, 0, notice)
          return { ...state, messages }
        }
        case 'conversation.loaded': {
          // The chat's canvas replaces the current one.
          const cards = ev.cards.map(({ id, kind, title, data }) => ({ id, kind, title, data }))
          return {
            ...state,
            messages: ev.messages.map((m) => ({ ...m, id: nextLocalId(), done: true, model: m.model || undefined })),
            cards,
            selectedImage: null,
            stageTab: cards.some((c) => c.kind !== 'model3d') ? 'cards' : 'core',
          }
        }
        case 'chats.list':
          return { ...state, savedChats: ev.chats, maxSavedChats: ev.max }
        case 'canvas.card': {
          const card: CanvasCard = { id: ev.id, kind: ev.kind, title: ev.title, data: ev.data }
          const i = state.cards.findIndex((c) => c.id === ev.id)
          const cards = i === -1 ? [...state.cards, card] : state.cards.map((c, j) => (j === i ? card : c))
          // A selected image got a new version: keep "this one" pointing at the latest.
          let selectedImage = state.selectedImage
          if (ev.kind === 'image' && selectedImage?.id === ev.id) {
            selectedImage = { id: ev.id, version: (ev.data as unknown as ImageCardData).current }
          }
          // A 3D model opens (or comes back to) its own tab; other cards open the
          // cards tab, unless you're looking at a 3D model.
          // A video's progress updates don't pull you back to the canvas.
          const onModel = state.cards.some((c) => c.kind === 'model3d' && c.id === state.stageTab)
          const progressOnly = ev.kind === 'video' && i !== -1 && (ev.data as unknown as VideoCardData).status === 'rendering'
          const stageTab = ev.kind === 'model3d' ? ev.id : onModel || progressOnly ? state.stageTab : 'cards'
          return { ...state, cards, selectedImage, stageTab }
        }
        case 'settings.state': {
          const { type: _type, ...settings } = ev
          return { ...state, settings }
        }
        case 'usage.update': {
          const { type: _type, ...usage } = ev
          return { ...state, usage }
        }
        case 'notice':
          return {
            ...state,
            messages: [...state.messages, { id: nextLocalId(), role: 'notice', text: ev.message, info: true }],
          }
        case 'error':
          if (ev.id) {
            return {
              ...state,
              messages: updateMessage(state.messages, ev.id, (m) => ({ ...m, error: ev.message })),
            }
          }
          return {
            ...state,
            messages: [...state.messages, { id: nextLocalId(), role: 'notice', text: ev.message }],
          }
      }
    }
  }
  return state
}

const initialState: ChatState = {
  messages: [],
  connection: 'connecting',
  busy: false,
  activeTool: null,
  modelOverride: null,
  cards: [],
  stageTab: 'core',
  selectedImage: null,
  settings: null,
  usage: null,
  savedChats: [],
  maxSavedChats: 5,
  log: [],
}

export function useJarvis() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const socketRef = useRef<JarvisSocket | null>(null)
  const overrideRef = useRef<ModelAlias | null>(null)

  useEffect(() => {
    const socket = new JarvisSocket()
    socket.onEvent = (ev) => dispatch({ kind: 'server', ev })
    socket.onConnection = (s) => dispatch({ kind: 'connection', state: s })
    // Settings live per connection on the server, so re-send them after a reconnect.
    socket.onOpen = () => {
      if (overrideRef.current) {
        socket.send({ type: 'settings.update', model_override: overrideRef.current })
      }
    }
    socket.connect()
    socketRef.current = socket
    return () => socket.close()
  }, [])

  const sendText = useCallback((text: string, files: Attachment[] = []) => {
    const trimmed = text.trim()
    if (!trimmed && files.length === 0) return false
    if (!socketRef.current?.send({ type: 'user.text', text: trimmed, files: files.map((f) => f.id) })) return false
    dispatch({ kind: 'user', text: trimmed, files })
    return true
  }, [])

  const setModelOverride = useCallback((model: ModelAlias | null) => {
    overrideRef.current = model
    dispatch({ kind: 'override', model })
    socketRef.current?.send({ type: 'settings.update', model_override: model })
  }, [])

  const answerConfirm = useCallback((id: string, approved: boolean) => {
    if (socketRef.current?.send({ type: 'user.confirm', id, approved })) {
      dispatch({ kind: 'answer', id, approved })
    }
  }, [])

  const setProvider = useCallback((provider: Provider) => {
    socketRef.current?.send({ type: 'settings.update', provider })
  }, [])

  const setGatewayModel = useCallback((gateway_model: string) => {
    socketRef.current?.send({ type: 'settings.update', gateway_model })
  }, [])

  const newChat = useCallback(() => {
    socketRef.current?.send({ type: 'user.new_chat' })
  }, [])

  const { messages, cards } = state
  const saveChat = useCallback(() => {
    socketRef.current?.send({ type: 'user.save_chat', messages, cards })
  }, [messages, cards])

  const loadChat = useCallback((id: string) => {
    socketRef.current?.send({ type: 'user.load_chat', id })
  }, [])

  const deleteChat = useCallback((id: string) => {
    socketRef.current?.send({ type: 'user.delete_chat', id })
  }, [])

  const closeCard = useCallback((id: string) => dispatch({ kind: 'closeCard', id }), [])
  const selectImage = useCallback(
    (selection: ImageSelection | null) => dispatch({ kind: 'select', selection }),
    [],
  )

  // Keep the server in step with what you've selected (also after a reconnect).
  const selectedImage = state.selectedImage
  const connected = state.connection === 'open'
  useEffect(() => {
    if (!connected) return
    socketRef.current?.send(
      selectedImage
        ? { type: 'user.select_image', id: selectedImage.id, version: selectedImage.version }
        : { type: 'user.select_image', id: null },
    )
  }, [selectedImage, connected])
  const setStageTab = useCallback((tab: string) => dispatch({ kind: 'tab', tab }), [])

  return { ...state, sendText, newChat, saveChat, loadChat, deleteChat, setProvider, setGatewayModel, setModelOverride, answerConfirm, closeCard, selectImage, setStageTab }
}
