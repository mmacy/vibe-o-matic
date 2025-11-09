import { describe, it, expect } from 'vitest'
import { findRuleExcerpt, extractExcerptFromSection, trimToMaxLength } from '../src/lib/pdf/excerpt'

describe('findRuleExcerpt', () => {
  const rulesText = `
    COMBAT
    When combat begins, roll initiative.
    Each character takes a turn in order.

    SAVING THROWS
    Characters make saving throws to avoid danger.
    Roll 1d20 and add modifiers.
  `

  it('should find relevant excerpt based on keywords', () => {
    const excerpt = findRuleExcerpt(rulesText, ['combat', 'initiative'])
    expect(excerpt).toContain('combat')
    expect(excerpt.length).toBeLessThanOrEqual(256)
  })

  it('should return message when no match found', () => {
    const excerpt = findRuleExcerpt(rulesText, ['nonexistent'])
    expect(excerpt).toContain('No matching rule')
  })

  it('should trim to max length', () => {
    const longText = 'A'.repeat(500)
    const excerpt = findRuleExcerpt(longText, ['A'])
    expect(excerpt.length).toBeLessThanOrEqual(256)
  })
})

describe('extractExcerptFromSection', () => {
  const text = `
    # COMBAT
    When combat begins, roll initiative.

    # MAGIC
    Spellcasters can cast spells.
  `

  it('should extract specific section', () => {
    const excerpt = extractExcerptFromSection(text, 'COMBAT')
    expect(excerpt).toContain('initiative')
  })

  it('should return message when section not found', () => {
    const excerpt = extractExcerptFromSection(text, 'UNKNOWN')
    expect(excerpt).toContain('not found')
  })
})

describe('trimToMaxLength', () => {
  it('should not trim short text', () => {
    const text = 'Short text'
    expect(trimToMaxLength(text)).toBe(text)
  })

  it('should trim long text', () => {
    const text = 'A'.repeat(300)
    const trimmed = trimToMaxLength(text)
    expect(trimmed.length).toBe(256)
    expect(trimmed).toContain('...')
  })
})
