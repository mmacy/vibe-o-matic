import { describe, it, expect } from 'vitest'
import { parseDiceExpr, canonicalizeDiceExpr } from '../src/lib/dice/parse'

describe('parseDiceExpr', () => {
  it('should parse simple dice expressions', () => {
    const result = parseDiceExpr('1d20')
    expect(result).toEqual({
      numDice: 1,
      diceSize: 20,
      modifier: 0,
      dropLowest: false,
      original: '1d20',
    })
  })

  it('should parse dice with positive modifier', () => {
    const result = parseDiceExpr('1d20+4')
    expect(result).toEqual({
      numDice: 1,
      diceSize: 20,
      modifier: 4,
      dropLowest: false,
      original: '1d20+4',
    })
  })

  it('should parse dice with negative modifier', () => {
    const result = parseDiceExpr('1d8-2')
    expect(result).toEqual({
      numDice: 1,
      diceSize: 8,
      modifier: -2,
      dropLowest: false,
      original: '1d8-2',
    })
  })

  it('should parse drop lowest notation', () => {
    const result = parseDiceExpr('4d6L')
    expect(result).toEqual({
      numDice: 4,
      diceSize: 6,
      modifier: 0,
      dropLowest: true,
      original: '4d6L',
    })
  })

  it('should parse drop lowest with modifier', () => {
    const result = parseDiceExpr('4d6+2L')
    expect(result).toEqual({
      numDice: 4,
      diceSize: 6,
      modifier: 2,
      dropLowest: true,
      original: '4d6+2L',
    })
  })

  it('should handle multiple dice', () => {
    const result = parseDiceExpr('3d8')
    expect(result).toEqual({
      numDice: 3,
      diceSize: 8,
      modifier: 0,
      dropLowest: false,
      original: '3d8',
    })
  })

  it('should throw error on invalid input', () => {
    expect(() => parseDiceExpr('invalid')).toThrow('Invalid dice expression')
  })

  it('should throw error on malformed expression', () => {
    expect(() => parseDiceExpr('1d20+X')).toThrow('Invalid dice expression')
  })

  it('should throw error on too many dice', () => {
    expect(() => parseDiceExpr('101d6')).toThrow('Invalid number of dice')
  })

  it('should throw error on invalid die size', () => {
    expect(() => parseDiceExpr('1d1')).toThrow('Invalid die size')
  })
})

describe('canonicalizeDiceExpr', () => {
  it('should canonicalize simple expression', () => {
    const parsed = parseDiceExpr('1d20')
    expect(canonicalizeDiceExpr(parsed)).toBe('1d20')
  })

  it('should canonicalize with positive modifier', () => {
    const parsed = parseDiceExpr('1d20+4')
    expect(canonicalizeDiceExpr(parsed)).toBe('1d20+4')
  })

  it('should canonicalize with negative modifier', () => {
    const parsed = parseDiceExpr('1d8-2')
    expect(canonicalizeDiceExpr(parsed)).toBe('1d8-2')
  })

  it('should canonicalize drop lowest', () => {
    const parsed = parseDiceExpr('4d6L')
    expect(canonicalizeDiceExpr(parsed)).toBe('4d6L')
  })
})
