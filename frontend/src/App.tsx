import { useState } from 'react'
import './App.css'
import Chat from './components/Chat'
import Panel from './components/Panel'
import { LogPanel, TerminalPanel, UsagePanel } from './components/SidePanels'
import Stage from './components/Stage'
import TopBar from './components/TopBar'
import { useSwipePanes } from './useSwipePanes'
import { useJarvis } from './ws'

const PANES = [['chat', 'CHAT'], ['stage', 'CANVAS'], ['status', 'STATUS']] as const
const PANE_IDS = PANES.map(([id]) => id)

// HUD layout: chat on the left, the core / canvas in the middle, status on the right.
// A phone shows one of the three at a time (App.css): drag sideways (useSwipePanes), or
// use the bar at the bottom.
export default function App() {
  const jarvis = useJarvis()
  const [pane, setPane] = useState<(typeof PANES)[number][0]>('chat')
  const [voiceOn, setVoiceOn] = useState(false) // UI only for now (Phase 5a)
  const { ref: gridRef, go, touch } = useSwipePanes(PANE_IDS, pane, setPane)

  return (
    <div className="hud">
      <TopBar
        connection={jarvis.connection}
        busy={jarvis.busy}
        settings={jarvis.settings}
        canStartNewChat={!jarvis.busy && jarvis.connection === 'open' && jarvis.messages.length > 0}
        onNewChat={jarvis.newChat}
        onProvider={jarvis.setProvider}
        savedChats={jarvis.savedChats}
        maxSavedChats={jarvis.maxSavedChats}
        canSaveChat={!jarvis.busy && jarvis.connection === 'open' && jarvis.messages.length > 0}
        canLoadChat={!jarvis.busy && jarvis.connection === 'open'}
        onSaveChat={jarvis.saveChat}
        onLoadChat={jarvis.loadChat}
        onDeleteChat={jarvis.deleteChat}
        memories={jarvis.memories}
        memoryCategories={jarvis.memoryCategories}
        onSaveMemory={jarvis.saveMemory}
        onDeleteMemory={jarvis.deleteMemory}
        onWipeMemory={jarvis.wipeMemory}
        jobs={jarvis.jobs}
        jobRuns={jarvis.jobRuns}
        onJob={jarvis.updateJob}
      />

      <main className={`hud-grid pane-${pane}`} ref={gridRef} {...touch}>
        <Panel title="COMMS" tag="RT-LINK" className="comms-panel">
          <Chat
            messages={jarvis.messages}
            connection={jarvis.connection}
            busy={jarvis.busy}
            activeTool={jarvis.activeTool}
            onSend={jarvis.sendText}
            onConfirm={jarvis.answerConfirm}
            voiceOn={voiceOn}
            onVoice={setVoiceOn}
          />
        </Panel>

        <Stage
          cards={jarvis.cards}
          tab={jarvis.stageTab}
          onTab={jarvis.setStageTab}
          onClose={jarvis.closeCard}
          selectedImage={jarvis.selectedImage}
          onSelectImage={jarvis.selectImage}
          terminals={jarvis.terminals}
          onCloseTerminal={jarvis.closeTerminal}
          busy={jarvis.busy}
          activeTool={jarvis.activeTool}
          connection={jarvis.connection}
          voiceOn={voiceOn}
          onVoice={setVoiceOn}
        />

        <div className="hud-right">
          <UsagePanel
            usage={jarvis.usage}
            settings={jarvis.settings}
            modelOverride={jarvis.modelOverride}
            onModel={jarvis.setModelOverride}
            onGatewayModel={jarvis.setGatewayModel}
          />
          <LogPanel log={jarvis.log} />
          <TerminalPanel busy={jarvis.busy} activeTool={jarvis.activeTool} connection={jarvis.connection} />
        </div>
      </main>

      <nav className="hud-panes" aria-label="Sections">
        {PANES.map(([id, label]) => (
          <button key={id} type="button" className={pane === id ? 'active' : ''} aria-pressed={pane === id} onClick={() => go(id)}>
            {label}
            {id === 'stage' && jarvis.cards.length > 0 && <span className="count">{jarvis.cards.length}</span>}
          </button>
        ))}
      </nav>
    </div>
  )
}
