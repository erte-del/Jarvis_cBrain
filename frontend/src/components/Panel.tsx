// A HUD panel: "SYSTEM // TITLE" header, a tag on the right, corner brackets.

import type { ReactNode } from 'react'

interface PanelProps {
  title: string
  tag?: ReactNode
  className?: string
  children: ReactNode
}

export default function Panel({ title, tag, className = '', children }: PanelProps) {
  return (
    <section className={`panel ${className}`} aria-label={title}>
      <header className="panel-head">
        <div>
          <div className="panel-kicker">SYSTEM //</div>
          <div className="panel-title">{title}</div>
        </div>
        {tag && <div className="panel-tag">{tag}</div>}
      </header>
      <div className="panel-body">{children}</div>
    </section>
  )
}
