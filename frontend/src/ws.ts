// WebSocket client + event handling. Mirrors backend/events.py.

import { useCallback, useEffect, useReducer, useRef } from 'react'

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
    }
  | { type: 'tool.started'; id: string; name: string }
  | { type: 'tool.finished'; id: string; is_error: boolean }
  | { type: 'error'; message: string; id?: string }

// Browser -> server
export type ClientEvent =
  | { type: 'user.text'; text: string }
  | { type: 'settings.update'; model_override: ModelAlias | null }

export type ConnectionState = 'connecting' | 'open' | 'closed'

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
  role: 'user' | 'assistant' | 'notice'
  text: string
  model?: string // full model ID that answered (assistant only)
  reason?: string // why the router picked the model
  expert?: boolean // Opus was consulted via ask_expert
  done?: boolean
  error?: string
}

interface ChatState {
  messages: ChatMessage[]
  connection: ConnectionState
  busy: boolean // a reply is in progress
  activeTool: string | null
  modelOverride: ModelAlias | null
}

type Action =
  | { kind: 'server'; ev: ServerEvent }
  | { kind: 'connection'; state: ConnectionState }
  | { kind: 'user'; text: string }
  | { kind: 'override'; model: ModelAlias | null }

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

    case 'connection': {
      if (action.state !== 'closed' || state.connection === 'closed') {
        return { ...state, connection: action.state }
      }
      // Lost the connection: any reply in progress won't finish.
      const messages = state.messages.map((m) =>
        m.role === 'assistant' && !m.done && !m.error
          ? { ...m, error: 'Connection lost before the reply finished.' }
          : m,
      )
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
            })),
          }
        case 'tool.started':
          return { ...state, activeTool: ev.name }
        case 'tool.finished':
          return { ...state, activeTool: null }
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

  return { ...state, sendText, setModelOverride }
}
