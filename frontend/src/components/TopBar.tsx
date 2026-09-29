// HUD top bar: name, system status, local time, brain, New chat, saved chats and settings.

import { useEffect, useRef, useState } from 'react'
import { gatewayModelName } from '../labels'
import { useNow } from '../useNow'
import type { BrainSettings, ConnectionState, Provider, SavedChat } from '../ws'

interface TopBarProps {
  connection: ConnectionState
  busy: boolean
  settings: BrainSettings | null
  canStartNewChat: boolean
  onNewChat: () => void
  onProvider: (provider: Provider) => void
  savedChats: SavedChat[]
  maxSavedChats: number
  canSaveChat: boolean
  canLoadChat: boolean
  onSaveChat: () => void
  onLoadChat: (id: string) => void
  onDeleteChat: (id: string) => void
}

/** A menu under a top-bar button that closes on a click outside or Esc. */
function usePopup() {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => ref.current?.contains(e.target as Node) || setOpen(false)
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    window.addEventListener('mousedown', onClick)
    window.addEventListener('keydown', onKey)
    return () => {
      window.removeEventListener('mousedown', onClick)
      window.removeEventListener('keydown', onKey)
    }
  }, [open])
  return { open, setOpen, ref }
}

function SavedChats(props: Pick<TopBarProps, 'savedChats' | 'maxSavedChats' | 'canSaveChat' | 'canLoadChat' | 'onSaveChat' | 'onLoadChat' | 'onDeleteChat'>) {
  const { open, setOpen, ref } = usePopup()
  const { savedChats, maxSavedChats } = props

  return (
    <div className="settings" ref={ref}>
      <button
        type="button"
        className={`icon-btn${open ? ' active' : ''}`}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="Saved chats"
        title="Saved chats"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <path d="M5 3h11l3 3v15H5z" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
          <path d="M8 3v5h7V3M8 21v-7h8v7" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round" />
        </svg>
      </button>
      {open && (
        <div className="settings-menu" role="dialog" aria-label="Saved chats">
          <div className="settings-head">
            SAVED CHATS · {savedChats.length}/{maxSavedChats}
          </div>
          <button
            type="button"
            className="provider"
            onClick={() => {
              props.onSaveChat()
              setOpen(false)
            }}
            disabled={!props.canSaveChat}
          >
            <span className="provider-name">Save this chat</span>
            <span className="provider-note">
              Saving it again later updates the same slot.
            </span>
          </button>
          {savedChats.map((chat) => (
            <div key={chat.id} className="saved-chat">
              <button
                type="button"
                className="provider"
                disabled={!props.canLoadChat}
                onClick={() => {
                  props.onLoadChat(chat.id)
                  setOpen(false)
                }}
              >
                <span className="provider-name">{chat.title}</span>
                <span className="provider-note">
                  {new Date(chat.saved_at * 1000).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                  {chat.provider === 'omniroute' && ' · OmniRoute'}
                </span>
              </button>
              <button
                type="button"
                className="icon-btn"
                onClick={() => props.onDeleteChat(chat.id)}
                aria-label={`Delete "${chat.title}"`}
                title="Delete"
              >
                ×
              </button>
            </div>
          ))}
          <div className="settings-foot">Loading a chat replaces the current conversation.</div>
        </div>
      )}
    </div>
  )
}

function Settings({ settings, onProvider }: Pick<TopBarProps, 'settings' | 'onProvider'>) {
  const { open, setOpen, ref } = usePopup()

  const choose = (provider: Provider) => {
    if (provider !== settings?.provider) onProvider(provider)
    setOpen(false)
  }

  return (
    <div className="settings" ref={ref}>
      <button
        type="button"
        className={`icon-btn${open ? ' active' : ''}`}
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-label="Settings"
        title="Settings"
      >
        <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
          <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
          <path
            d="M12 2.5v3M12 18.5v3M21.5 12h-3M5.5 12h-3M18.7 5.3l-2.1 2.1M7.4 16.6l-2.1 2.1M18.7 18.7l-2.1-2.1M7.4 7.4 5.3 5.3"
            stroke="currentColor"
            strokeWidth="1.8"
            strokeLinecap="round"
          />
        </svg>
      </button>
      {open && (
        <div className="settings-menu" role="dialog" aria-label="Brain">
          <div className="settings-head">BRAIN</div>
          <button
            type="button"
            className={`provider${settings?.provider !== 'omniroute' ? ' active' : ''}`}
            onClick={() => choose('claude')}
          >
            <span className="provider-name">Claude · Pro login</span>
            <span className="provider-note">
              Sonnet by default, Haiku or Opus when useful. Uses your Pro limit. Gmail and your other connectors are on.
            </span>
          </button>
          <button
            type="button"
            className={`provider${settings?.provider === 'omniroute' ? ' active' : ''}`}
            onClick={() => choose('omniroute')}
          >
            <span className="provider-name">OmniRoute</span>
            <span className="provider-note">
              Your OmniRoute models ({settings?.gateway_models.map((m) => gatewayModelName(m).provider).join(', ')}) through{' '}
              {settings?.gateway_url ?? 'OmniRoute'}. Switch between them with the model buttons.
              Doesn't use your Pro limit. Connectors and web search are off, and tools may work less reliably.
            </span>
          </button>
          <div className="settings-foot">Switching starts a new conversation.</div>
        </div>
      )}
    </div>
  )
}

export default function TopBar({ connection, busy, settings, canStartNewChat, onNewChat, onProvider, ...chats }: TopBarProps) {
  const now = useNow()
  const status =
    connection === 'open' ? (busy ? 'PROCESSING' : 'ONLINE') : connection === 'connecting' ? 'CONNECTING' : 'OFFLINE'

  return (
    <header className="hud-top">
      <div className="hud-brand">
        <span className="hud-logo" aria-hidden="true" />
        <div>
          <div className="hud-name">JARVIS</div>
          <div className="hud-motto">JUST A RATHER VERY INTELLIGENT SYSTEM</div>
        </div>
      </div>

      <div className="hud-readouts">
        <div>
          <div className="readout-key">SYSTEM STATUS</div>
          <div className={`readout-val status-${connection}`}>
            <span className="status-dot" />
            {status}
          </div>
        </div>
        <div>
          <div className="readout-key">LOCAL TIME</div>
          <div className="readout-val">{now.toLocaleTimeString([], { hour12: false })}</div>
        </div>
        <div>
          <div className="readout-key">BRAIN</div>
          <div className="readout-val">
            {settings?.provider === 'omniroute'
              ? `OMNIROUTE · ${gatewayModelName(settings.gateway_model).provider.toUpperCase()}`
              : 'CLAUDE · PRO'}
          </div>
        </div>
      </div>

      <div className="hud-actions">
        <button
          type="button"
          className="icon-btn"
          onClick={onNewChat}
          disabled={!canStartNewChat}
          aria-label="New chat"
          title="New chat. Long conversations use more of your limit with every message."
        >
          <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
            <path d="M4 5h11M4 5v14h14V9" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
            <path d="M18 2v6M15 5h6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
          </svg>
        </button>
        <SavedChats {...chats} />
        <Settings settings={settings} onProvider={onProvider} />
      </div>
    </header>
  )
}
