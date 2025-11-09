/**
 * Dice expression parser
 * Supports format: NdM[+/-K][L]
 * Examples: 1d20, 1d20+4, 4d6L, 3d8-2
 */

export interface ParsedDiceExpr {
  numDice: number
  diceSize: number
  modifier: number
  dropLowest: boolean
  original: string
}

/**
 * Parse a dice expression string into components
 * Throws an error if the expression is invalid
 */
export function parseDiceExpr(expr: string): ParsedDiceExpr {
  const trimmed = expr.trim()
  const dropLowest = trimmed.toUpperCase().endsWith('L')
  const base = dropLowest ? trimmed.slice(0, -1) : trimmed

  // Match pattern: NdM[+/-K]
  const match = base.match(/^(\d+)d(\d+)(([+-])(\d+))?$/i)

  if (!match) {
    throw new Error(
      `Invalid dice expression: "${expr}". Expected format: NdM[+/-K][L] (e.g., 1d20, 1d20+4, 4d6L)`
    )
  }

  const numDice = parseInt(match[1])
  const diceSize = parseInt(match[2])
  const modifierSign = match[4] || '+'
  const modifierValue = match[5] ? parseInt(match[5]) : 0
  const modifier = modifierSign === '-' ? -modifierValue : modifierValue

  // Validate reasonable ranges
  if (numDice < 1 || numDice > 100) {
    throw new Error(`Invalid number of dice: ${numDice}. Must be between 1 and 100.`)
  }
  if (diceSize < 2 || diceSize > 1000) {
    throw new Error(`Invalid die size: ${diceSize}. Must be between 2 and 1000.`)
  }

  return {
    numDice,
    diceSize,
    modifier,
    dropLowest,
    original: expr,
  }
}

/**
 * Convert parsed dice expression back to canonical string form
 */
export function canonicalizeDiceExpr(parsed: ParsedDiceExpr): string {
  let result = `${parsed.numDice}d${parsed.diceSize}`

  if (parsed.modifier > 0) {
    result += `+${parsed.modifier}`
  } else if (parsed.modifier < 0) {
    result += `${parsed.modifier}`
  }

  if (parsed.dropLowest) {
    result += 'L'
  }

  return result
}
