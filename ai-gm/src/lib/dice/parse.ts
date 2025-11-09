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
 */
export function parseDiceExpr(expr: string): ParsedDiceExpr {
  const trimmed = expr.trim()
  const dropLowest = trimmed.toUpperCase().endsWith('L')
  const base = dropLowest ? trimmed.slice(0, -1) : trimmed

  // Match pattern: NdM[+/-K]
  const match = base.match(/^(\d+)d(\d+)(([+-])(\d+))?$/i)

  if (!match) {
    // Try to simplify to nearest recognized form
    // If it contains 'd', try to extract dice components
    if (base.includes('d')) {
      const parts = base.split('d')
      const numDice = parseInt(parts[0]) || 1
      const remaining = parts[1] || '20'
      const diceMatch = remaining.match(/^(\d+)/)
      const diceSize = diceMatch ? parseInt(diceMatch[1]) : 20

      return {
        numDice,
        diceSize,
        modifier: 0,
        dropLowest,
        original: expr,
      }
    }

    // Default to d20 if unparseable
    return {
      numDice: 1,
      diceSize: 20,
      modifier: 0,
      dropLowest: false,
      original: expr,
    }
  }

  const numDice = parseInt(match[1])
  const diceSize = parseInt(match[2])
  const modifierSign = match[4] || '+'
  const modifierValue = match[5] ? parseInt(match[5]) : 0
  const modifier = modifierSign === '-' ? -modifierValue : modifierValue

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
