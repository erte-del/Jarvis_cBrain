// Voice state orb: idle / listening / thinking / speaking. (Phase 5)

import type { CSSProperties } from 'react'

export type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking'

interface VoiceOrbProps {
  state: VoiceState
  level?: number // 0..1, how loud you are (listening) or Jarvis is (speaking)
  onClick?: () => void
  label: string
}

export default function VoiceOrb({ state, level = 0, onClick, label }: VoiceOrbProps) {
  return (
    <button
      type="button"
      className={`orb orb-${state}`}
      style={{ '--level': Math.max(0, Math.min(1, level)) } as CSSProperties}
      onClick={onClick}
      aria-label={label}
      title={label}
    >
      <span className="orb-ring" />
      <span className="orb-ring" />
      <span className="orb-ring" />
      <span className="orb-spin" />
      <span className="orb-core" />
    </button>
  )
}
