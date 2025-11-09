import { describe, it, expect, vi, beforeEach } from 'vitest'
import { executeDiceRoll } from '../src/lib/dice/roll'
import type { ParsedDiceExpr } from '../src/lib/dice/parse'

describe('executeDiceRoll', () => {
  beforeEach(() => {
    // Mock Math.random for deterministic tests
    let callCount = 0
    vi.spyOn(Math, 'random').mockImplementation(() => {
      const values = [0.5, 0.2, 0.8, 0.1, 0.9]
      return values[callCount++ % values.length]
    })
  })

  it('should roll a single die', () => {
    const parsed: ParsedDiceExpr = {
      numDice: 1,
      diceSize: 20,
      modifier: 0,
      dropLowest: false,
      original: '1d20',
    }

    const result = executeDiceRoll(parsed)
    expect(result.total).toBeGreaterThanOrEqual(1)
    expect(result.total).toBeLessThanOrEqual(20)
    expect(result.rolls).toHaveLength(1)
  })

  it('should apply modifiers correctly', () => {
    const parsed: ParsedDiceExpr = {
      numDice: 1,
      diceSize: 20,
      modifier: 4,
      dropLowest: false,
      original: '1d20+4',
    }

    const result = executeDiceRoll(parsed)
    expect(result.total).toBeGreaterThanOrEqual(5) // 1 + 4
    expect(result.total).toBeLessThanOrEqual(24) // 20 + 4
  })

  it('should handle drop lowest', () => {
    const parsed: ParsedDiceExpr = {
      numDice: 4,
      diceSize: 6,
      modifier: 0,
      dropLowest: true,
      original: '4d6L',
    }

    const result = executeDiceRoll(parsed)
    expect(result.rolls).toHaveLength(4)
    expect(result.total).toBeGreaterThanOrEqual(3) // Minimum 3 ones, drop one
    expect(result.total).toBeLessThanOrEqual(18) // Maximum 3 sixes
  })

  it('should include detail string', () => {
    const parsed: ParsedDiceExpr = {
      numDice: 1,
      diceSize: 20,
      modifier: 4,
      dropLowest: false,
      original: '1d20+4',
    }

    const result = executeDiceRoll(parsed)
    expect(result.detail).toContain('d20')
    expect(result.detail).toContain('+4')
  })
})
