// Right-hand HUD panels: usage (plan limit + tokens + model), system log, terminal.

import { useEffect, useRef } from 'react'
import { toolLabel } from '../labels'
import { useNow } from '../useNow'
import type { ActiveTool, BrainSettings, ConnectionState, LogLine, ModelAlias, UsageSnapshot, UsageWindow } from '../ws'
import Panel from './Panel'

const fmt = (n: number) =>
  n >= 1_000_000 ? `${(n / 1_000_000).toFixed(1)}M` : n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n)

function countdown(resetsAt: number, now: Date): string {
  const mins = Math.max(0, Math.round((resetsAt * 1000 - now.getTime()) / 60000))
  const h = Math.floor(mins / 60)
  if (h >= 24) return `in ${Math.floor(h / 24)}d ${h % 24}h`
  return h > 0 ? `in ${h}h ${mins % 60}m` : `in ${mins}m`
}

function resetTime(resetsAt: number): string {
  const d = new Date(resetsAt * 1000)
  const sameDay = d.toDateString() === new Date().toDateString()
  const time = d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
  return sameDay ? time : `${d.toLocaleDateString([], { weekday: 'short' })} ${time}`
}

function Meter({ label, window, now }: { label: string; window?: UsageWindow; now: Date }) {
  if (!window) {
    return (
      <div className="meter">
        <div className="meter-label">{label}</div>
        <div className="meter-value dim">--</div>
        <div className="meter-bar" />
        <div className="meter-sub">after Jarvis's next reply</div>
      </div>
    )
  }
  const left = Math.max(0, 1 - window.used)
  const tone = left < 0.05 ? ' danger' : left < 0.2 ? ' warn' : ''
  return (
    <div className={`meter${tone}`}>
      <div className="meter-label">{label}</div>
      <div className="meter-value">{Math.round(left * 100)}%</div>
      <div className="meter-bar">
        <span style={{ width: `${left * 100}%` }} />
      </div>
      <div className="meter-sub">
        {window.resets_at ? `resets ${resetTime(window.resets_at)} · ${countdown(window.resets_at, now)}` : 'window just reset'}
      </div>
    </div>
  )
}

const MODELS: { id: ModelAlias | null; label: string; hint: string }[] = [
  { id: null, label: 'AUTO', hint: 'Jarvis picks (Sonnet by default)' },
  { id: 'haiku', label: 'HAIKU', hint: 'Fastest, cheapest' },
  { id: 'sonnet', label: 'SONNET', hint: 'The default' },
  { id: 'opus', label: 'OPUS', hint: 'Strongest, uses the most of your limit' },
]

interface UsagePanelProps {
  usage: UsageSnapshot | null
  settings: BrainSettings | null
  modelOverride: ModelAlias | null
  onModel: (model: ModelAlias | null) => void
}

export function UsagePanel({ usage, settings, modelOverride, onModel }: UsagePanelProps) {
  const now = useNow(30_000)
  const onClaude = settings?.provider !== 'omniroute'
  const t = usage?.tokens
  const total = t ? t.input + t.cache_write + t.cache_read + t.output : 0

  return (
    <Panel title="USAGE" tag={onClaude ? 'PRO PLAN' : 'OMNIROUTE'} className="usage-panel">
      {onClaude ? (
        <div className="meters">
          <Meter label="5-HOUR LIMIT LEFT" window={usage?.windows.five_hour} now={now} />
          <Meter label="WEEKLY LIMIT LEFT" window={usage?.windows.seven_day} now={now} />
        </div>
      ) : (
        <div className="usage-note">OmniRoute doesn't use your Pro limit.</div>
      )}

      <div className="usage-section">
        <div className="usage-label">JARVIS · THIS 5-HOUR WINDOW</div>
        <div className="usage-total">
          {fmt(total)} <span>tokens</span>
        </div>
        <dl className="usage-rows" title="Cache reads cost about a tenth of new input">
          <div><dt>New input</dt><dd>{fmt(t?.input ?? 0)}</dd></div>
          <div><dt>Cache writes</dt><dd>{fmt(t?.cache_write ?? 0)}</dd></div>
          <div><dt>Cache reads</dt><dd>{fmt(t?.cache_read ?? 0)}</dd></div>
          <div><dt>Output</dt><dd>{fmt(t?.output ?? 0)}</dd></div>
          <div className="usage-conv"><dt>This conversation</dt><dd>{fmt(usage?.context_tokens ?? 0)}</dd></div>
        </dl>
      </div>

      <div className="usage-label">{onClaude ? 'MODEL' : `MODEL · ${settings?.gateway_model ?? 'auto'}`}</div>
      <div className="model-buttons">
        {MODELS.map((m) => (
          <button
            key={m.label}
            type="button"
            className={`model-btn model-${m.id ?? 'auto'}${modelOverride === m.id ? ' active' : ''}`}
            onClick={() => onModel(m.id)}
            disabled={!onClaude}
            aria-pressed={modelOverride === m.id}
            title={onClaude ? m.hint : 'OmniRoute picks the model'}
          >
            <span className="model-dot" />
            {m.label}
          </button>
        ))}
      </div>
    </Panel>
  )
}

export function LogPanel({ log }: { log: LogLine[] }) {
  const listRef = useRef<HTMLOListElement>(null)
  useEffect(() => {
    const list = listRef.current
    if (list) list.scrollTop = list.scrollHeight
  }, [log])

  return (
    <Panel title="LOG" tag="RT-LOG" className="log-panel">
      <ol className="log" ref={listRef}>
        {log.length === 0 && <li className="log-empty">No activity yet.</li>}
        {log.map((l) => (
          <li key={l.id} className={l.tone ? `log-${l.tone}` : undefined}>
            <time>[{l.time}]</time> {l.text}
          </li>
        ))}
      </ol>
    </Panel>
  )
}

const COMMANDS: Record<string, string> = {
  WebSearch: 'search',
  WebFetch: 'fetch',
  ToolSearch: 'find-tool',
  ask_expert: 'consult-opus',
  show_on_canvas: 'display',
  preview_3d: 'build-3d --preview',
  export_3d: 'build-3d --final',
}

interface TerminalPanelProps {
  busy: boolean
  activeTool: ActiveTool | null
  connection: ConnectionState
}

export function TerminalPanel({ busy, activeTool, connection }: TerminalPanelProps) {
  let command: string
  let status: string
  if (connection !== 'open') {
    command = 'jarvis --reconnect'
    status = connection === 'closed' ? 'Backend offline. Waiting for it to come back…' : 'Connecting…'
  } else if (activeTool) {
    const cmd = COMMANDS[activeTool.name] ?? activeTool.name.replace(/_/g, '-').toLowerCase()
    command = `jarvis --${cmd}${activeTool.detail ? ` "${activeTool.detail}"` : ''}`
    status = toolLabel(activeTool)
  } else if (busy) {
    command = 'jarvis --process'
    status = 'Working on your request…'
  } else {
    command = 'jarvis --await-input'
    status = 'Standing by.'
  }

  return (
    <Panel title="TERMINAL" tag="ROOT@JARVIS" className="terminal-panel">
      <div className="terminal">
        <div className="terminal-cmd">
          <span className="prompt">&gt;_</span> {command}
          {!busy && connection === 'open' && <span className="terminal-cursor" />}
        </div>
        <div className="terminal-status">{status}</div>
      </div>
    </Panel>
  )
}
