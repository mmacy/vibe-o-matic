import { DiceRollInputSchema, CreateCharacterInputSchema } from '@/app/state/schema'
import { zodFunction } from 'openai/helpers/zod'

/**
 * Define the roll_dice function tool
 */
export const rollDiceTool = zodFunction({
  name: 'roll_dice',
  description:
    'Execute a dice roll for B/X play. Use this for all dice rolls - never simulate or make up results.',
  parameters: DiceRollInputSchema,
})

/**
 * Define the create_character function tool
 */
export const createCharacterTool = zodFunction({
  name: 'create_character',
  description:
    'Add a new character to the party. Use this when a player creates a character during guided character creation.',
  parameters: CreateCharacterInputSchema,
})

/**
 * All available function tools
 */
export const tools = [rollDiceTool, createCharacterTool]
