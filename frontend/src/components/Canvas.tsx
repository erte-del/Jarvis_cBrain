// Canvas: images, 3D objects and cards. (Phase 4a)
// Text, table, email list and events cards. Later steps add images and 3D.

import type { CanvasCard } from '../ws'
import Markdown from './Markdown'

interface CanvasProps {
  cards: CanvasCard[]
  onClose: (id: string) => void
}

function TableCard({ data }: { data: Record<string, unknown> }) {
  const columns = (data.columns as string[]) ?? []
  const rows = (data.rows as string[][]) ?? []
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th key={i}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, r) => (
            <tr key={r}>
              {row.map((cell, c) => (
                <td key={c}>{cell}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

type Item = Record<string, string>

const isUnread = (v?: string) => v === 'true' || v === 'True' || v === '1'

function EmailList({ items }: { items: Item[] }) {
  return (
    <ul className="email-list">
      {items.map((m, i) => (
        <li key={m.id ?? i} className={isUnread(m.unread) ? 'unread' : undefined}>
          <div className="email-top">
            <span className="email-from">{m.from}</span>
            <span className="email-date">{m.date}</span>
          </div>
          <div className="email-subject">{m.subject || '(no subject)'}</div>
          {m.snippet && <div className="email-snippet">{m.snippet}</div>}
        </li>
      ))}
    </ul>
  )
}

function Events({ items }: { items: Item[] }) {
  return (
    <ul className="event-list">
      {items.map((e, i) => (
        <li key={i}>
          <div className="event-when">
            {e.start}
            {e.end && <> – {e.end}</>}
          </div>
          <div className="event-title">{e.title}</div>
          {e.location && <div className="event-meta">{e.location}</div>}
          {e.notes && <div className="event-meta">{e.notes}</div>}
        </li>
      ))}
    </ul>
  )
}

function CardBody({ card }: { card: CanvasCard }) {
  switch (card.kind) {
    case 'text':
      return (
        <div className="card-text">
          <Markdown text={String(card.data.content ?? '')} />
        </div>
      )
    case 'table':
      return <TableCard data={card.data} />
    case 'email_list':
      return <EmailList items={(card.data.items as Item[]) ?? []} />
    case 'events':
      return <Events items={(card.data.items as Item[]) ?? []} />
    default:
      return <pre className="card-raw">{JSON.stringify(card.data, null, 2)}</pre>
  }
}

export default function Canvas({ cards, onClose }: CanvasProps) {
  return (
    <aside className="canvas" aria-label="Canvas">
      {cards.length === 0 ? (
        <div className="canvas-empty">Things Jarvis shows you will appear here.</div>
      ) : (
        [...cards].reverse().map((card) => (
          <section key={card.id} className="card">
            <header className="card-head">
              <span className="card-title">{card.title}</span>
              <span className="card-id">{card.id}</span>
              <button className="card-close" onClick={() => onClose(card.id)} aria-label="Close card">
                ×
              </button>
            </header>
            <CardBody card={card} />
          </section>
        ))
      )}
    </aside>
  )
}
