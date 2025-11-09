'use client'

import { useState } from 'react'

interface DiceAuditProps {
  rolls: Array<{
    source: string
    action: string
    target?: string
    total: number
    expr: string
  }>
}

export default function DiceAudit({ rolls }: DiceAuditProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  if (rolls.length === 0) return null

  return (
    <div className="mt-4 border-t border-slate-700 pt-4">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="mb-2 flex items-center gap-2 font-bold text-text hover:text-text-muted"
      >
        <span className="text-xs">{isExpanded ? '▼' : '▶'}</span>
        <span>Dice audit</span>
      </button>
      {isExpanded && (
        <ul className="list-disc space-y-1 pl-5 text-sm text-text-muted">
          {rolls.map((roll, index) => (
            <li key={index}>
              {roll.source} {roll.action}
              {roll.target ? ` ${roll.target}` : ''}: <strong>{roll.total}</strong>{' '}
              <span className="font-mono">({roll.expr})</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
