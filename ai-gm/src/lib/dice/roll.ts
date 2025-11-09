import { parseDiceExpr, canonicalizeDiceExpr, ParsedDiceExpr } from './parse'
import type { DiceRollInput, DiceRollOutput } from '@/app/state/schema'

/**
 * Roll a single die
 */
function rollDie(size: number): number {
  return Math.floor(Math.random() * size) + 1
}

/**
 * Roll multiple dice and return individual results
 */
function rollDice(numDice: number, diceSize: number): number[] {
  const results: number[] = []
  for (let i = 0; i < numDice; i++) {
    results.push(rollDie(diceSize))
  }
  return results
}

/**
 * Execute a dice roll based on parsed expression
 */
export function executeDiceRoll(parsed: ParsedDiceExpr): {
  total: number
  detail: string
  rolls: number[]
} {
  let rolls = rollDice(parsed.numDice, parsed.diceSize)

  // Handle drop lowest
  if (parsed.dropLowest && rolls.length > 1) {
    const minIndex = rolls.indexOf(Math.min(...rolls))
    const kept = [...rolls]
    kept.splice(minIndex, 1)

    const keptSum = kept.reduce((sum, val) => sum + val, 0)
    const total = keptSum + parsed.modifier

    const detail = `d${parsed.diceSize}=${JSON.stringify(rolls)}→keep ${JSON.stringify(kept)}→${keptSum}${parsed.modifier !== 0 ? (parsed.modifier > 0 ? '+' + parsed.modifier : parsed.modifier) : ''}`

    return { total, detail, rolls }
  }

  // Normal roll
  const rollSum = rolls.reduce((sum, val) => sum + val, 0)
  const total = rollSum + parsed.modifier

  let detail = `d${parsed.diceSize}=${JSON.stringify(rolls)}`
  if (parsed.modifier !== 0) {
    detail += parsed.modifier > 0 ? `+${parsed.modifier}` : `${parsed.modifier}`
  }

  return { total, detail, rolls }
}

/**
 * Main dice rolling function used by the tool
 */
export function rollDice_tool(input: DiceRollInput): DiceRollOutput {
  const parsed = parseDiceExpr(input.expr)
  const result = executeDiceRoll(parsed)
  const normalized = canonicalizeDiceExpr(parsed)

  return {
    total: result.total,
    detail: result.detail,
    normalized_expr: normalized,
  }
}
