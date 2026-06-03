import React, { useState } from 'react'

const DEMO_CHIPS = [
  {
    label: 'Monday order',
    query: 'what should i order this monday',
  },
  {
    label: 'Strawberries in June',
    query: 'are strawberries still worth ordering in june',
  },
  {
    label: "Queen's Birthday week",
    query: "queens birthday is next week how do i adjust",
  },
  {
    label: 'Leftover strawberries',
    query: 'we have leftover strawberries from friday what do we do',
  },
  {
    label: 'Order mangoes',
    query: 'should i order mangoes this week',
  },
  {
    label: 'Best performers this month',
    query: 'which items have been our best performers this month',
  },
]

export default function DemoChips({ onSelect, visible }) {
  const [hiding, setHiding] = useState(false)

  function handleClick(chip) {
    setHiding(true)
    onSelect(chip.query)
  }

  if (!visible) return null

  return (
    <div
      className={`px-4 pb-3 transition-all duration-500 ${hiding ? 'opacity-0 -translate-y-2 pointer-events-none' : 'opacity-100 translate-y-0'}`}
    >
      <p className="text-xs text-text-secondary mb-2 font-mono">Try a demo query:</p>
      <div className="flex flex-wrap gap-2">
        {DEMO_CHIPS.map((chip) => (
          <button
            key={chip.label}
            onClick={() => handleClick(chip)}
            className="px-3 py-1.5 rounded-full border border-border bg-surface text-xs text-text-secondary hover:text-text-primary hover:border-accent/50 hover:bg-accent/5 transition-all duration-200 font-mono"
          >
            {chip.label}
          </button>
        ))}
      </div>
    </div>
  )
}
