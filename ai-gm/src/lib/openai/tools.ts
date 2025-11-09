import { DiceRollInputSchema } from '@/app/state/schema'
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
 * All available function tools
 */
export const tools = [rollDiceTool]
