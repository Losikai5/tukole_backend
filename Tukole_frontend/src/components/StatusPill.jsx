const toneMap = {
  accepted: 'blue',
  admin: 'violet',
  cancelled: 'rose',
  completed: 'green',
  escrow: 'violet',
  open: 'amber',
  pending: 'amber',
  provider: 'blue',
  refunded: 'rose',
  released: 'green',
  rejected: 'rose',
  resolved: 'green',
  under_review: 'blue',
  unread: 'amber',
  user: 'teal',
}

export function formatStatusLabel(value) {
  if (!value) {
    return 'Unknown'
  }

  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase())
}

export function StatusPill({ status }) {
  const tone = toneMap[status] || 'slate'

  return <span className={`status-pill status-pill--${tone}`}>{formatStatusLabel(status)}</span>
}
