// Confirmation card for 'act' tools. (Phase 4a)
// Jarvis wants to send / delete / create / change something: nothing happens until you approve.

import type { Confirmation, ConfirmStatus } from '../ws'

interface ConfirmCardProps {
  confirm: Confirmation
  onAnswer: (approved: boolean) => void
}

const STATUS_LABEL: Record<ConfirmStatus, string> = {
  pending: 'Waiting for you',
  approved: 'Approved',
  denied: 'Declined',
  expired: 'Expired — not done',
}

export default function ConfirmCard({ confirm, onAnswer }: ConfirmCardProps) {
  const pending = confirm.status === 'pending'
  return (
    <div className={`confirm-card confirm-${confirm.status}`} role="group" aria-label="Confirmation">
      <div className="confirm-head">
        <span className="confirm-icon" aria-hidden>
          !
        </span>
        <span className="confirm-title">{confirm.title}</span>
        {!pending && <span className="confirm-status">{STATUS_LABEL[confirm.status]}</span>}
      </div>

      {confirm.details.length > 0 && (
        <dl className="confirm-details">
          {confirm.details.map(([label, value]) => (
            <div key={label} className="confirm-row">
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}

      {pending && (
        <div className="confirm-actions">
          <button className="btn-approve" onClick={() => onAnswer(true)}>
            Approve
          </button>
          <button className="btn-deny" onClick={() => onAnswer(false)}>
            Deny
          </button>
        </div>
      )}
    </div>
  )
}
