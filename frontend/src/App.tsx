import { useState } from 'react'
import './App.css'
import Chat from './components/Chat'
import Panel from './components/Panel'
import { LogPanel, TerminalPanel, UsagePanel } from './components/SidePanels'
import Stage from './components/Stage'
import TopBar from './components/TopBar'
import { useJarvis } from './ws'

// HUD layout: chat on the left, the core / canvas in the middle, status on the right.
export default function App() {
  const jarvis = useJarvis()
  const [voiceOn, setVoiceOn] = useState(false) // UI only for now (Phase 5a)

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
      />

      <main className="hud-grid">
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
    </div>
  )
}
