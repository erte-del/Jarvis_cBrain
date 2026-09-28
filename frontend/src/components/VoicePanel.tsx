// Voice mode panel above the input box: the orb, what's happening, live captions.
// UI only for now: the preview buttons switch between the states so you can see
// them. Step 5b onwards drives the state from the microphone and the backend.

import { useState } from 'react'
import VoiceOrb, { type VoiceState } from './VoiceOrb'

const STATES: VoiceState[] = ['idle', 'listening', 'thinking', 'speaking']

const STATUS: Record<VoiceState, { title: string; hint: string; orb: string }> = {
  idle: { title: 'Mic paused', hint: 'Click the orb to start talking.', orb: 'Start listening' },
  listening: { title: 'Listening…', hint: 'Speak naturally. Jarvis answers when you pause.', orb: 'Pause the mic' },
  thinking: { title: 'Thinking…', hint: 'You can keep typing below.', orb: 'Thinking' },
  speaking: { title: 'Speaking…', hint: 'Click the orb to interrupt.', orb: 'Stop speaking' },
}

// Sample captions so the preview looks like the real thing.
const SAMPLE: Record<VoiceState, { you?: string; jarvis?: string }> = {
  idle: {},
  listening: { you: "What's on my calendar tomorrow" },
  thinking: { you: "What's on my calendar tomorrow?" },
  speaking: {
    you: "What's on my calendar tomorrow?",
    jarvis: 'You have three things tomorrow. The first is a dentist appointment at nine.',
  },
}

interface VoicePanelProps {
  onClose: () => void
}

export default function VoicePanel({ onClose }: VoicePanelProps) {
  const [state, setState] = useState<VoiceState>('listening')
  const status = STATUS[state]
  const sample = SAMPLE[state]
  const next = () => setState(STATES[(STATES.indexOf(state) + 1) % STATES.length])

  return (
    <section className={`voice-panel voice-${state}`} aria-label="Voice mode" aria-live="polite">
      <div className="voice-main">
        <VoiceOrb state={state} onClick={next} label={status.orb} />
        <div className="voice-side">
          <div className="voice-title">{status.title}</div>
          {sample.you && (
            <div className={`voice-caption voice-you${state === 'listening' ? ' interim' : ''}`}>
              <span className="voice-who">You</span>
              {sample.you}
            </div>
          )}
          {sample.jarvis && (
            <div className="voice-caption voice-jarvis">
              <span className="voice-who">Jarvis</span>
              {sample.jarvis}
            </div>
          )}
          <div className="voice-hint">{status.hint}</div>
        </div>
        <button type="button" className="voice-close" onClick={onClose} title="End voice mode (Esc)">
          End voice
        </button>
      </div>
      <div className="voice-preview">
        <span>UI preview (voice isn't connected yet):</span>
        {STATES.map((s) => (
          <button
            key={s}
            type="button"
            className={`voice-preview-chip${s === state ? ' active' : ''}`}
            onClick={() => setState(s)}
          >
            {s}
          </button>
        ))}
      </div>
    </section>
  )
}
