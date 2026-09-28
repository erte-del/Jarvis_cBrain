import './App.css'
import Chat from './components/Chat'
import { useJarvis, type ModelAlias } from './ws'

const CONNECTION_LABEL = {
  open: 'Connected',
  connecting: 'Connecting…',
  closed: 'Backend offline',
} as const

export default function App() {
  const jarvis = useJarvis()

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          Jarvis
        </div>
        <div className="topbar-right">
          <label className="model-picker">
            Model
            <select
              value={jarvis.modelOverride ?? 'auto'}
              onChange={(e) =>
                jarvis.setModelOverride(e.target.value === 'auto' ? null : (e.target.value as ModelAlias))
              }
            >
              <option value="auto">Auto</option>
              <option value="haiku">Haiku</option>
              <option value="sonnet">Sonnet</option>
              <option value="opus">Opus</option>
            </select>
          </label>
          <span className={`conn conn-${jarvis.connection}`}>{CONNECTION_LABEL[jarvis.connection]}</span>
        </div>
      </header>

      <Chat
        messages={jarvis.messages}
        connection={jarvis.connection}
        busy={jarvis.busy}
        activeTool={jarvis.activeTool}
        onSend={jarvis.sendText}
      />
    </div>
  )
}
