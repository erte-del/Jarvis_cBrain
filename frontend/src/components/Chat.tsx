// Message list, input box, streaming replies, model badge.

import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ChatMessage, ConnectionState } from '../ws'

interface ChatProps {
  messages: ChatMessage[]
  connection: ConnectionState
  busy: boolean
  activeTool: string | null
  onSend: (text: string) => boolean
}

/** "claude-haiku-4-5-20251001" -> "Haiku" */
function modelFamily(modelId: string): 'haiku' | 'sonnet' | 'opus' | 'other' {
  const id = modelId.toLowerCase()
  if (id.includes('haiku')) return 'haiku'
  if (id.includes('sonnet')) return 'sonnet'
  if (id.includes('opus')) return 'opus'
  return 'other'
}

function ModelBadge({ model }: { model: string }) {
  const family = modelFamily(model)
  const label = family === 'other' ? model : family[0].toUpperCase() + family.slice(1)
  return (
    <span className={`model-badge model-${family}`} title={model}>
      {label}
    </span>
  )
}

function Message({ message }: { message: ChatMessage }) {
  if (message.role === 'notice') {
    return <div className="notice">{message.text}</div>
  }
  if (message.role === 'user') {
    return (
      <div className="msg msg-user">
        <div className="bubble">{message.text}</div>
      </div>
    )
  }
  return (
    <div className="msg msg-assistant">
      <div className="bubble">
        {message.text && (
          <Markdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: (props) => <a {...props} target="_blank" rel="noreferrer noopener" />,
            }}
          >
            {message.text}
          </Markdown>
        )}
        {!message.done && !message.error && <span className="cursor" />}
        {message.error && <div className="msg-error">{message.error}</div>}
      </div>
      {message.model && <ModelBadge model={message.model} />}
    </div>
  )
}

export default function Chat({ messages, connection, busy, activeTool, onSend }: ChatProps) {
  const [draft, setDraft] = useState('')
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const stickToBottom = useRef(true)

  // Keep the newest text in view, unless you've scrolled up to read something.
  useEffect(() => {
    const list = listRef.current
    if (list && stickToBottom.current) list.scrollTop = list.scrollHeight
  }, [messages, busy])

  const onScroll = () => {
    const list = listRef.current
    if (list) stickToBottom.current = list.scrollHeight - list.scrollTop - list.clientHeight < 40
  }

  const canSend = connection === 'open' && !busy && draft.trim() !== ''

  const submit = () => {
    if (!canSend) return
    if (onSend(draft)) {
      setDraft('')
      stickToBottom.current = true
    }
  }

  const onKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit()
    }
  }

  // Refocus the input when a reply finishes.
  useEffect(() => {
    if (!busy) inputRef.current?.focus()
  }, [busy])

  const last = messages[messages.length - 1]
  const waitingForFirstWord = busy && (!last || last.role === 'user')

  return (
    <div className="chat">
      <div className="messages" ref={listRef} onScroll={onScroll}>
        {messages.length === 0 && (
          <div className="empty">
            <div className="empty-title">Good day.</div>
            <div>What can I do for you?</div>
          </div>
        )}
        {messages.map((m) => (
          <Message key={m.id} message={m} />
        ))}
        {waitingForFirstWord && (
          <div className="msg msg-assistant">
            <div className="bubble typing">
              {activeTool ? `Using ${activeTool}…` : <><span /><span /><span /></>}
            </div>
          </div>
        )}
      </div>

      <form
        className="composer"
        onSubmit={(e) => {
          e.preventDefault()
          submit()
        }}
      >
        <textarea
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={connection === 'open' ? 'Message Jarvis…' : 'Waiting for the backend…'}
          rows={1}
          autoFocus
        />
        <button type="submit" disabled={!canSend} aria-label="Send">
          ↑
        </button>
      </form>
    </div>
  )
}
