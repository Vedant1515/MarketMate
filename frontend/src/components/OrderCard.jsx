import React, { useCallback } from 'react'

function vsNormalDisplay(pct) {
  if (pct == null) return { text: '-', className: 'text-text-secondary' }
  if (pct > 0) return { text: `+${pct.toFixed(0)}%`, className: 'text-accent' }
  if (pct < 0) return { text: `${pct.toFixed(0)}%`, className: 'text-danger' }
  return { text: 'stable', className: 'text-text-secondary' }
}

function confidenceBadge(conf) {
  switch (conf) {
    case 'High':
      return 'text-accent'
    case 'Medium':
      return 'text-warning'
    case 'Low':
      return 'text-danger'
    default:
      return 'text-text-secondary'
  }
}

function buildPlainTextOrder(order) {
  const lines = [
    'MarketMate Order Recommendation',
    '='.repeat(60),
    `${'Item'.padEnd(18)} ${'Qty'.padStart(7)} ${'Unit'.padEnd(8)} ${'vs Normal'.padStart(10)} ${'Conf'.padEnd(8)} Reasoning`,
    '-'.repeat(90),
  ]
  for (const item of order.items) {
    const vs = item.vs_normal_pct > 0
      ? `+${item.vs_normal_pct.toFixed(0)}%`
      : item.vs_normal_pct < 0
        ? `${item.vs_normal_pct.toFixed(0)}%`
        : 'stable'
    const qty = item.quantity === 0 ? 'SKIP' : item.quantity.toFixed(1)
    lines.push(
      `${item.item.padEnd(18)} ${qty.padStart(7)} ${item.unit.padEnd(8)} ${vs.padStart(10)} ${item.confidence.padEnd(8)} ${(item.reasoning || '').slice(0, 45)}`
    )
  }
  lines.push('-'.repeat(90))
  lines.push(
    `${'TOTALS'.padEnd(18)} ${''.padStart(7)} ${''.padEnd(8)} ${''.padStart(10)} ${''.padEnd(8)} Cost: $${order.total_cost_aud?.toFixed(2)} | Revenue: $${order.total_revenue_aud?.toFixed(2)}`
  )
  lines.push('')
  lines.push(`Order by: ${order.order_by}`)
  lines.push(`Confidence: ${order.confidence}`)
  if (order.notes) lines.push(`Notes: ${order.notes}`)
  return lines.join('\n')
}

export default function OrderCard({ order }) {
  const handleExport = useCallback(() => {
    const text = buildPlainTextOrder(order)
    navigator.clipboard.writeText(text).catch(() => {
      const el = document.createElement('textarea')
      el.value = text
      document.body.appendChild(el)
      el.select()
      document.execCommand('copy')
      document.body.removeChild(el)
    })
  }, [order])

  if (!order || !order.items) return null

  return (
    <div className="mt-4 rounded-xl border border-border bg-surface overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div>
          <span className="text-sm font-semibold text-text-primary">Order Recommendation</span>
          <span className="ml-2 text-xs text-text-secondary font-mono">
            {order.items.length} items
          </span>
        </div>
        <button
          onClick={handleExport}
          className="text-xs px-3 py-1.5 rounded-lg border border-border text-text-secondary hover:text-text-primary hover:border-accent/50 transition-colors font-mono"
        >
          Export as text
        </button>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full font-mono text-xs">
          <thead>
            <tr className="border-b border-border">
              <th className="text-left px-4 py-2 text-text-secondary font-medium">Item</th>
              <th className="text-right px-3 py-2 text-text-secondary font-medium">Qty</th>
              <th className="text-left px-3 py-2 text-text-secondary font-medium">Unit</th>
              <th className="text-right px-3 py-2 text-text-secondary font-medium">vs Normal</th>
              <th className="text-left px-3 py-2 text-text-secondary font-medium">Conf</th>
              <th className="text-left px-3 py-2 text-text-secondary font-medium hidden md:table-cell">Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {order.items.map((item, i) => {
              const vs = vsNormalDisplay(item.vs_normal_pct)
              const isSkip = item.quantity === 0
              return (
                <tr
                  key={i}
                  className={`border-b border-border/50 hover:bg-background/50 transition-colors ${isSkip ? 'opacity-50' : ''}`}
                >
                  <td className={`px-4 py-2 text-text-primary font-medium ${isSkip ? 'line-through text-text-secondary' : ''}`}>
                    {item.item}
                  </td>
                  <td className="px-3 py-2 text-right text-text-primary">
                    {isSkip ? (
                      <span className="text-danger font-semibold">SKIP</span>
                    ) : (
                      item.quantity.toFixed(1)
                    )}
                  </td>
                  <td className="px-3 py-2 text-text-secondary">{item.unit}</td>
                  <td className={`px-3 py-2 text-right font-semibold ${isSkip ? 'text-danger line-through' : vs.className}`}>
                    {isSkip ? 'SKIP' : vs.text}
                  </td>
                  <td className={`px-3 py-2 ${confidenceBadge(item.confidence)}`}>
                    {item.confidence}
                  </td>
                  <td className="px-3 py-2 text-text-secondary hidden md:table-cell max-w-xs truncate">
                    {item.reasoning}
                  </td>
                </tr>
              )
            })}
          </tbody>
          <tfoot>
            <tr className="border-t border-border bg-background/30">
              <td colSpan={2} className="px-4 py-2 text-text-secondary font-semibold">
                Totals
              </td>
              <td colSpan={2} className="px-3 py-2 text-text-secondary text-right">
                Cost: <span className="text-text-primary">${order.total_cost_aud?.toFixed(2)}</span>
              </td>
              <td colSpan={2} className="px-3 py-2 text-text-secondary">
                Revenue: <span className="text-accent">${order.total_revenue_aud?.toFixed(2)}</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>

      <div className="px-4 py-3 border-t border-border space-y-1">
        <div className="flex items-center gap-4 text-xs">
          <span className="text-text-secondary">
            Order by: <span className="text-text-primary font-mono">{order.order_by}</span>
          </span>
          <span className="text-text-secondary">
            Confidence: <span className="text-accent">{order.confidence}</span>
          </span>
        </div>
        {order.notes && (
          <p className="text-xs text-text-secondary italic">{order.notes}</p>
        )}
      </div>
    </div>
  )
}
