import { z } from 'zod'

// Journal front-matter schema
export const JournalFrontMatterSchema = z.object({
  schema_version: z.string().default('1.0'),
  system: z.enum(['BX', 'OSE']),
  party: z.array(
    z.object({
      name: z.string(),
      class: z.string(),
      level: z.number(),
      hp: z.number(),
      max_hp: z.number(),
      abilities: z.object({
        str: z.number(),
        int: z.number(),
        wis: z.number(),
        dex: z.number(),
        con: z.number(),
        cha: z.number(),
      }),
      inventory: z.array(z.string()).default([]),
      ac: z.number(),
      thac0: z.number().optional(),
      xp: z.number().default(0),
    })
  ),
  flags: z.object({
    ability_scores_4d6L: z.boolean().default(false),
    level1_max_hp: z.boolean().default(false),
  }),
  module_id: z.string().optional(),
  created_at: z.string(),
  updated_at: z.string(),
})

export type JournalFrontMatter = z.infer<typeof JournalFrontMatterSchema>

// Dice roll tool schema
export const DiceRollInputSchema = z.object({
  expr: z.string().describe('Dice expression in format NdM[+/-K][L]'),
  source: z.string().describe('Actor or source of the roll'),
  action: z.string().describe('What the roll represents'),
  target: z.string().optional().describe('Target of the action, if any'),
})

export type DiceRollInput = z.infer<typeof DiceRollInputSchema>

export const DiceRollOutputSchema = z.object({
  total: z.number().describe('Final result after all modifiers'),
  detail: z.string().describe('Breakdown of the roll'),
  normalized_expr: z.string().describe('Canonicalized expression'),
})

export type DiceRollOutput = z.infer<typeof DiceRollOutputSchema>

// Character creation tool schema (matches party member structure)
export const CreateCharacterInputSchema = z.object({
  name: z.string().describe('Character name'),
  class: z.string().describe('Character class'),
  level: z.number().describe('Character level'),
  hp: z.number().describe('Current hit points'),
  max_hp: z.number().describe('Maximum hit points'),
  abilities: z.object({
    str: z.number().describe('Strength'),
    int: z.number().describe('Intelligence'),
    wis: z.number().describe('Wisdom'),
    dex: z.number().describe('Dexterity'),
    con: z.number().describe('Constitution'),
    cha: z.number().describe('Charisma'),
  }).describe('Ability scores'),
  inventory: z.array(z.string()).default([]).describe('Starting inventory items'),
  ac: z.number().describe('Armor class'),
  thac0: z.number().optional().describe('To-hit AC 0 (optional)'),
  xp: z.number().default(0).describe('Experience points'),
})

export type CreateCharacterInput = z.infer<typeof CreateCharacterInputSchema>

// Chat message schema
export const ChatMessageSchema = z.object({
  id: z.string(),
  role: z.enum(['user', 'assistant', 'system']),
  content: z.string(),
  timestamp: z.string(),
  dice_audit: z
    .array(
      z.object({
        source: z.string(),
        action: z.string(),
        target: z.string().optional(),
        total: z.number(),
        expr: z.string(),
      })
    )
    .optional(),
})

export type ChatMessage = z.infer<typeof ChatMessageSchema>

// Settings schema
export const SettingsSchema = z.object({
  ability_scores_4d6L: z.boolean().default(false),
  level1_max_hp: z.boolean().default(false),
  model: z.string().default('gpt-4o-2024-08-06'),
})

export type Settings = z.infer<typeof SettingsSchema>

// Journal entry cache schema (for in-memory collection before AI summarization)
export const JournalEntryCacheSchema = z.object({
  userMessage: z.string(),
  gmResponse: z.string(),
  timestamp: z.string(),
  diceAudit: z
    .array(
      z.object({
        source: z.string(),
        action: z.string(),
        target: z.string().optional(),
        total: z.number(),
        expr: z.string(),
      })
    )
    .optional(),
  createdCharacters: z.array(CreateCharacterInputSchema).optional(),
})

export type JournalEntryCache = z.infer<typeof JournalEntryCacheSchema>
