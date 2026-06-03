import React from 'react'

const LEVEL_STYLES = {
  Low: {
    bg: 'bg-green-900/40',
    border: 'border-green-700',
    text: 'text-green-400',
    dot: 'bg-green-500',
  },
  Medium: {
    bg: 'bg-amber-900/40',
    border: 'border-amber-700',
    text: 'text-amber-400',
    dot: 'bg-amber-500',
  },
  High: {
    bg: 'bg-orange-900/40',
    border: 'border-orange-700',
    text: 'text-orange-400',
    dot: 'bg-orange-500',
  },
  Critical: {
    bg: 'bg-red-900/40',
    border: 'border-red-700',
    text: 'text-red-400',
    dot: 'bg-red-500',
  },
}

export default function SpoilageAlert({ level, item, quantity }) {
  const styles = LEVEL_STYLES[level] || LEVEL_STYLES.Low

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full border text-xs font-medium ${styles.bg} ${styles.border} ${styles.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
      {level} risk
      {item && <span className="text-text-secondary">- {item}</span>}
      {quantity != null && (
        <span className="text-text-secondary">({quantity})</span>
      )}
    </span>
  )
}
