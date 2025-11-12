import { describe, it, expect } from 'vitest'
import { normalizeCharacterForJournal, CreateCharacterInputSchema, JournalFrontMatterSchema } from '@/app/state/schema'
import type { CreateCharacterInput } from '@/app/state/schema'
import { serializeJournal } from '@/lib/journal/serialize'
import { parseJournal } from '@/lib/journal/parse'

describe('normalizeCharacterForJournal', () => {
  it('should convert null inventory to empty array', () => {
    const character: CreateCharacterInput = {
      name: 'Test Fighter',
      class: 'Fighter',
      level: 1,
      hp: 8,
      max_hp: 8,
      abilities: { str: 16, int: 10, wis: 12, dex: 14, con: 15, cha: 10 },
      inventory: null,
      ac: 5,
      thac0: 19,
      xp: 0,
    }

    const normalized = normalizeCharacterForJournal(character)
    expect(normalized.inventory).toEqual([])
  })

  it('should convert null xp to 0', () => {
    const character: CreateCharacterInput = {
      name: 'Test Wizard',
      class: 'Magic-User',
      level: 1,
      hp: 4,
      max_hp: 4,
      abilities: { str: 8, int: 16, wis: 12, dex: 10, con: 10, cha: 12 },
      inventory: ['spellbook', 'dagger'],
      ac: 10,
      thac0: 19,
      xp: null,
    }

    const normalized = normalizeCharacterForJournal(character)
    expect(normalized.xp).toBe(0)
  })

  it('should convert null thac0 to undefined', () => {
    const character: CreateCharacterInput = {
      name: 'Test Cleric',
      class: 'Cleric',
      level: 1,
      hp: 6,
      max_hp: 6,
      abilities: { str: 12, int: 10, wis: 16, dex: 10, con: 14, cha: 13 },
      inventory: ['mace', 'holy symbol'],
      ac: 4,
      thac0: null,
      xp: 100,
    }

    const normalized = normalizeCharacterForJournal(character)
    expect(normalized.thac0).toBeUndefined()
  })

  it('should preserve non-null values', () => {
    const character: CreateCharacterInput = {
      name: 'Test Thief',
      class: 'Thief',
      level: 2,
      hp: 10,
      max_hp: 10,
      abilities: { str: 10, int: 12, wis: 10, dex: 18, con: 12, cha: 14 },
      inventory: ['lockpicks', 'rope', 'dagger'],
      ac: 7,
      thac0: 19,
      xp: 1500,
    }

    const normalized = normalizeCharacterForJournal(character)
    expect(normalized.inventory).toEqual(['lockpicks', 'rope', 'dagger'])
    expect(normalized.xp).toBe(1500)
    expect(normalized.thac0).toBe(19)
  })

  it('should produce a character that passes JournalFrontMatter validation', () => {
    const character: CreateCharacterInput = {
      name: 'Test Character',
      class: 'Fighter',
      level: 1,
      hp: 8,
      max_hp: 8,
      abilities: { str: 16, int: 10, wis: 12, dex: 14, con: 15, cha: 10 },
      inventory: null,
      ac: 5,
      thac0: null,
      xp: null,
    }

    const normalized = normalizeCharacterForJournal(character)

    // Should validate as part of a journal front matter
    const frontMatter = {
      schema_version: '1.0',
      system: 'BX' as const,
      party: [normalized],
      flags: {
        ability_scores_4d6L: false,
        level1_max_hp: false,
      },
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }

    expect(() => JournalFrontMatterSchema.parse(frontMatter)).not.toThrow()
  })

  it('should survive a full journal serialize/parse round-trip', () => {
    const character: CreateCharacterInput = {
      name: 'Round Trip Test',
      class: 'Magic-User',
      level: 3,
      hp: 12,
      max_hp: 12,
      abilities: { str: 8, int: 18, wis: 12, dex: 14, con: 10, cha: 12 },
      inventory: null, // Null from API
      ac: 10,
      thac0: null, // Null from API
      xp: null, // Null from API
    }

    const normalized = normalizeCharacterForJournal(character)

    // Create a minimal journal
    const journal = {
      frontMatter: {
        schema_version: '1.0',
        system: 'BX' as const,
        party: [normalized],
        flags: {
          ability_scores_4d6L: false,
          level1_max_hp: false,
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      },
      sessionLog: [],
      characters: '',
      inventory: '',
      houseRules: '',
    }

    // Serialize to markdown/YAML
    const serialized = serializeJournal(journal)

    // Parse it back
    const parsed = parseJournal(serialized)

    // Character should survive round-trip
    expect(parsed.frontMatter.party).toHaveLength(1)
    expect(parsed.frontMatter.party[0].name).toBe('Round Trip Test')
    expect(parsed.frontMatter.party[0].inventory).toEqual([])
    expect(parsed.frontMatter.party[0].xp).toBe(0)
    expect(parsed.frontMatter.party[0].thac0).toBeUndefined()
  })
})
