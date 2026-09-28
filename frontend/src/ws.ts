// WebSocket client + event handling. Mirrors backend/events.py.

import { useCallback, useEffect, useReducer, useRef } from 'react'

export const API_BASE = 'http://127.0.0.1:8000'
const WS_URL = 'ws://127.0.0.1:8000/ws'

export type ModelAlias = 'haiku' | 'sonnet' | 'opus'

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
  | { type: 'confirm.request'; id: string; title: string; summary: string; details: [string, string][] }
  | { type: 'confirm.resolved'; id: string; status: ConfirmStatus }
  | { type: 'canvas.card'; id: string; kind: string; title: string; data: Record<string, unknown> }

// Browser -> server
export type ClientEvent =
  | { type: 'user.text'; text: string }
  | { type: 'user.confirm'; id: string; approved: boolean }
  | { type: 'user.select_image'; id: string | null; version?: number }
  | { type: 'settings.update'; model_override: ModelAlias | null }

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
  confirm?: Confirmation // role 'confirm': an action waiting for your approval
  model?: string // full model ID that answered (assistant only)
  reason?: string // why the router picked the model
  expert?: boolean // Opus was consulted via ask_expert
  sources?: Source[]
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
  canvasOpen: boolean
  canvasTab: string // 'cards', or the id of a 3D model shown in its own tab
  selectedImage: ImageSelection | null
}

type Action =
  | { kind: 'server'; ev: ServerEvent }
  | { kind: 'connection'; state: ConnectionState }
  | { kind: 'user'; text: string }
  | { kind: 'override'; model: ModelAlias | null }
  | { kind: 'answer'; id: string; approved: boolean }
  | { kind: 'closeCard'; id: string }
  | { kind: 'toggleCanvas' }
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

function reducer(state: ChatState, action: Action): ChatState {
  switch (action.kind) {
    case 'user':
      return {
        ...state,
        busy: true,
        messages: [...state.messages, { id: nextLocalId(), role: 'user', text: action.text }],
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
      const canvasTab = state.canvasTab === action.id ? 'cards' : state.canvasTab
      return { ...state, cards, selectedImage, canvasTab, canvasOpen: state.canvasOpen && cards.length > 0 }
    }

    case 'tab':
      return { ...state, canvasTab: action.tab }

    case 'select':
      return { ...state, selectedImage: action.selection }

    case 'toggleCanvas':
      return { ...state, canvasOpen: !state.canvasOpen }

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
        case 'canvas.card': {
          const card: CanvasCard = { id: ev.id, kind: ev.kind, title: ev.title, data: ev.data }
          const i = state.cards.findIndex((c) => c.id === ev.id)
          const cards = i === -1 ? [...state.cards, card] : state.cards.map((c, j) => (j === i ? card : c))
          // A selected image got a new version: keep "this one" pointing at the latest.
          let selectedImage = state.selectedImage
          if (ev.kind === 'image' && selectedImage?.id === ev.id) {
            selectedImage = { id: ev.id, version: (ev.data as unknown as ImageCardData).current }
          }
          // A 3D model opens (or comes back to) its own big tab.
          const canvasTab = ev.kind === 'model3d' ? ev.id : state.canvasTab
          return { ...state, cards, selectedImage, canvasTab, canvasOpen: true }
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
  canvasOpen: false,
  canvasTab: 'cards',
  selectedImage: null,
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

  const sendText = useCallback((text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return false
    if (!socketRef.current?.send({ type: 'user.text', text: trimmed })) return false
    dispatch({ kind: 'user', text: trimmed })
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
  const toggleCanvas = useCallback(() => dispatch({ kind: 'toggleCanvas' }), [])
  const setCanvasTab = useCallback((tab: string) => dispatch({ kind: 'tab', tab }), [])

  return { ...state, sendText, setModelOverride, answerConfirm, closeCard, toggleCanvas, selectImage, setCanvasTab }
}
