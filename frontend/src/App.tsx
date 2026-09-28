import './App.css'
import Canvas from './components/Canvas'
import Chat from './components/Chat'
import { useJarvis, type ModelAlias } from './ws'

const CONNECTION_LABEL = {
  open: 'Connected',
  connecting: 'Connecting…',
  closed: 'Backend offline',
} as const

export default function App() {
  const jarvis = useJarvis()
  // A 3D model is open: its panel gets most of the width (chat stays usable on the left).
  const showingModel = jarvis.canvasOpen && jarvis.cards.some((c) => c.kind === 'model3d' && c.id === jarvis.canvasTab)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-dot" />
          Jarvis
        </div>
        <div className="topbar-right">
          <button
            className={`canvas-toggle${jarvis.canvasOpen ? ' active' : ''}`}
            onClick={jarvis.toggleCanvas}
            aria-pressed={jarvis.canvasOpen}
          >
            Canvas{jarvis.cards.length > 0 && <span className="count">{jarvis.cards.length}</span>}
          </button>
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

      <main className={`workspace${jarvis.canvasOpen ? ' with-canvas' : ''}${showingModel ? ' with-model' : ''}`}>
        <Chat
          messages={jarvis.messages}
          connection={jarvis.connection}
          busy={jarvis.busy}
          activeTool={jarvis.activeTool}
          onSend={jarvis.sendText}
          onConfirm={jarvis.answerConfirm}
        />
        {jarvis.canvasOpen && (
          <Canvas
            cards={jarvis.cards}
            onClose={jarvis.closeCard}
            selectedImage={jarvis.selectedImage}
            onSelectImage={jarvis.selectImage}
            tab={jarvis.canvasTab}
            onTab={jarvis.setCanvasTab}
          />
        )}
      </main>
    </div>
  )
}
