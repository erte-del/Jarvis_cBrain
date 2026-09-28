// Message list, input box, streaming replies, model badge.

import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import Markdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import type { ActiveTool, ChatMessage, ConnectionState, Source } from '../ws'

interface ChatProps {
  messages: ChatMessage[]
  connection: ConnectionState
  busy: boolean
  activeTool: ActiveTool | null
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

function toolLabel({ name, detail }: ActiveTool): string {
  switch (name) {
    case 'ask_expert':
      return 'Consulting Opus (expert)…'
    case 'WebSearch':
      return detail ? `Searching the web for “${detail}”…` : 'Searching the web…'
    case 'WebFetch':
      return detail ? `Reading ${detail}…` : 'Reading a web page…'
    default:
      return `Using ${name}…`
  }
}

// Claude ends web answers with a "Sources:" list of links. When we have the
// sources as chips, hide that list from the text.
const SOURCES_BLOCK =
  /\n+[ \t]*(?:#+[ \t]*)?(?:\*\*|__)?Sources?[ \t]*:?[ \t]*(?:\*\*|__)?[ \t]*:?[ \t]*\n(?:[ \t]*(?:[-*+]|\d+\.)[ \t]+.*(?:\n|$))+\s*$/i

const stripSourcesBlock = (text: string) => text.replace(SOURCES_BLOCK, '')

const domain = (url: string) => {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function SourceChips({ sources }: { sources: Source[] }) {
  const safe = sources.filter((s) => /^https?:\/\//i.test(s.url))
  if (safe.length === 0) return null
  return (
    <div className="sources">
      {safe.map((s) => (
        <a
          key={s.url}
          className="source-chip"
          href={s.url}
          target="_blank"
          rel="noreferrer noopener"
          title={s.title ? `${s.title}\n${s.url}` : s.url}
        >
          {domain(s.url)}
        </a>
      ))}
    </div>
  )
}

function Message({ message }: { message: ChatMessage }) {
  const hasSources = !!message.sources?.length
  const text = hasSources ? stripSourcesBlock(message.text) : message.text

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
        {text && (
          <Markdown
            remarkPlugins={[[remarkGfm, { singleTilde: false }]]} // "~$5" means "about $5", not strikethrough
            components={{
              a: (props) => <a {...props} target="_blank" rel="noreferrer noopener" />,
            }}
          >
            {text}
          </Markdown>
        )}
        {!message.done && !message.error && <span className="cursor" />}
        {message.error && <div className="msg-error">{message.error}</div>}
        {hasSources && <SourceChips sources={message.sources!} />}
      </div>
      {message.model && (
        <div className="msg-meta">
          <ModelBadge model={message.model} />
          {message.expert && (
            <span className="model-badge model-opus" title="Opus was consulted via ask_expert">
              + Opus
            </span>
          )}
          {message.reason && <span className="route-reason">{message.reason}</span>}
        </div>
      )}
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
  // A tool started after the reply already had some text (e.g. "Let me think…").
  const toolMidReply = busy && activeTool && last?.role === 'assistant' && !last.done

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
        {toolMidReply && <div className="activity">{toolLabel(activeTool)}</div>}
        {waitingForFirstWord && (
          <div className="msg msg-assistant">
            <div className="bubble typing">
              {activeTool ? toolLabel(activeTool) : <><span /><span /><span /></>}
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
