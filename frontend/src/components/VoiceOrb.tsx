// The reactor core in the middle of the HUD. It is also the voice orb: its rings
// show what Jarvis is doing (idle / listening / thinking / speaking). (Phase 5)

import type { CSSProperties } from 'react'

export type VoiceState = 'idle' | 'listening' | 'thinking' | 'speaking'

const CORE_TEXT: Record<VoiceState, [string, string]> = {
  idle: ['CORE', 'ACTIVE'],
  listening: ['VOICE', 'INPUT'],
  thinking: ['CORE', 'BUSY'],
  speaking: ['VOICE', 'OUTPUT'],
}

// A short bright arc on the ring of radius r, from angle a to b (degrees, 0 = up).
function arc(r: number, a: number, b: number): string {
  const point = (deg: number) => {
    const rad = ((deg - 90) * Math.PI) / 180
    return `${(r * Math.cos(rad)).toFixed(2)} ${(r * Math.sin(rad)).toFixed(2)}`
  }
  return `M ${point(a)} A ${r} ${r} 0 0 1 ${point(b)}`
}

const GRID = [-1, 0, 1].flatMap((y) => [-1, 0, 1].map((x) => ({ x, y })))

interface VoiceOrbProps {
  state: VoiceState
  level?: number // 0..1, how loud you are (listening) or Jarvis is (speaking)
  onClick?: () => void
  label: string
}

export default function VoiceOrb({ state, level = 0, onClick, label }: VoiceOrbProps) {
  const [line1, line2] = CORE_TEXT[state]
  return (
    <button
      type="button"
      className={`reactor reactor-${state}`}
      style={{ '--level': Math.max(0, Math.min(1, level)) } as CSSProperties}
      onClick={onClick}
      aria-label={label}
      title={label}
    >
      <svg viewBox="-200 -200 400 400" aria-hidden="true">
        <g className="r-outer">
          <circle r="190" className="r-dash" />
        </g>
        <g className="r-spokes">
          {[0, 60, 120].map((deg) => (
            <line key={deg} x1="0" y1="-196" x2="0" y2="196" transform={`rotate(${deg})`} />
          ))}
        </g>
        <circle r="166" className="r-line" />
        <circle r="124" className="r-line r-faint" />
        <g className="r-arcs">
          <path d={arc(166, -38, -26)} />
          <path d={arc(166, 142, 154)} />
        </g>
        <g className="r-ripples">
          <circle r="58" />
          <circle r="58" />
          <circle r="58" />
        </g>
        <circle r="58" className="r-core" />
        <g className="r-grid">
          {GRID.map(({ x, y }, i) => (
            <rect
              key={i}
              x={x * 24 - 6}
              y={y * 24 - 6}
              width="12"
              height="12"
              className={x === 0 && y === 0 ? 'r-cell r-cell-on' : 'r-cell'}
              style={{ animationDelay: `${i * 0.11}s` }}
            />
          ))}
        </g>
        <text className="r-text" y="-5">
          {line1}
        </text>
        <text className="r-text" y="20">
          {line2}
        </text>
      </svg>
    </button>
  )
}
