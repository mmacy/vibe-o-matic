import { describe, it, expect } from 'vitest'
import { serializeJournal, appendSessionLogEntry, updateParty } from '../src/lib/journal/serialize'
import { parseJournal, createDefaultJournal } from '../src/lib/journal/parse'
import type { Settings } from '../src/app/state/schema'

// Default settings for testing
const defaultSettings: Settings = {
  ability_scores_4d6L: false,
  level1_max_hp: false,
  model: 'gpt-4o-2024-08-06',
  temperature: 1,
  max_tokens: undefined,
  rules_pdf_path: undefined,
  module_pdf_path: undefined,
}

describe('serializeJournal', () => {
  it('should serialize default journal', () => {
    const journal = createDefaultJournal('BX', defaultSettings)

    const markdown = serializeJournal(journal)

    expect(markdown).toContain('---')
    expect(markdown).toContain('schema_version')
    expect(markdown).toContain('# Session log')
    expect(markdown).toContain('# Characters')
    expect(markdown).toContain('# Inventory')
    expect(markdown).toContain('# House rules')
  })

  it('should include party information', () => {
    const journal = createDefaultJournal('BX', defaultSettings)

    journal.frontMatter.party = [
      {
        name: 'Fighter',
        class: 'Fighter',
        level: 1,
        hp: 8,
        max_hp: 8,
        abilities: { str: 16, int: 10, wis: 12, dex: 14, con: 15, cha: 8 },
        inventory: [],
        ac: 5,
        xp: 0,
      },
    ]

    const markdown = serializeJournal(journal)
    expect(markdown).toContain('Fighter')
    expect(markdown).toContain('HP: 8/8')
  })

  it('should round-trip correctly', () => {
    const original = createDefaultJournal('BX', {
      ...defaultSettings,
      ability_scores_4d6L: true,
      level1_max_hp: true,
    })

    const markdown = serializeJournal(original)
    const parsed = parseJournal(markdown)

    expect(parsed.frontMatter.system).toBe('BX')
    expect(parsed.frontMatter.flags.ability_scores_4d6L).toBe(true)
    expect(parsed.frontMatter.flags.level1_max_hp).toBe(true)
  })
})

describe('appendSessionLogEntry', () => {
  it('should append entry to session log', () => {
    const journal = createDefaultJournal('BX', defaultSettings)

    const updated = appendSessionLogEntry(journal, 'The party entered the dungeon')
    expect(updated.sessionLog).toContain('The party entered the dungeon')
  })

  it('should update timestamp', async () => {
    const journal = createDefaultJournal('BX', defaultSettings)

    const originalTime = journal.frontMatter.updated_at

    // Small delay to ensure different timestamp
    await new Promise((resolve) => setTimeout(resolve, 10))

    const updated = appendSessionLogEntry(journal, 'Test entry')
    expect(updated.frontMatter.updated_at).not.toBe(originalTime)
  })
})

describe('updateParty', () => {
  it('should update party array', () => {
    const journal = createDefaultJournal('BX', defaultSettings)

    const newParty = [
      {
        name: 'Slick',
        class: 'Thief',
        level: 1,
        hp: 4,
        max_hp: 4,
        abilities: { str: 9, int: 13, wis: 10, dex: 16, con: 12, cha: 14 },
        inventory: ['Lockpicks', 'Dagger'],
        ac: 7,
        xp: 0,
      },
    ]

    const updated = updateParty(journal, newParty)
    expect(updated.frontMatter.party).toHaveLength(1)
    expect(updated.frontMatter.party[0].name).toBe('Slick')
  })

  it('should update timestamp when party changes', async () => {
    const journal = createDefaultJournal('BX', defaultSettings)

    const originalTime = journal.frontMatter.updated_at

    // Small delay to ensure different timestamp
    await new Promise((resolve) => setTimeout(resolve, 10))

    const updated = updateParty(journal, [])
    expect(updated.frontMatter.updated_at).not.toBe(originalTime)
  })
})
