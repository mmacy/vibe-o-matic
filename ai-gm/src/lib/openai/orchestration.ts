import OpenAI from 'openai'
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions'
import { rollDice_tool } from '@/lib/dice/roll'
import { DiceRollInputSchema, CreateCharacterInputSchema } from '@/app/state/schema'
import type { CreateCharacterInput } from '@/app/state/schema'
import { tools } from './tools'
import type { ParsedJournal } from '@/lib/journal/parse'

export interface GMRequest {
  client: OpenAI
  messages: ChatCompletionMessageParam[]
  rulesContext: string
  moduleContext: string
  journal?: ParsedJournal | null
  model?: string
  settings?: {
    ability_scores_4d6L?: boolean
    level1_max_hp?: boolean
    temperature?: number
    max_tokens?: number
  }
}

export interface GMResponse {
  text: string
  diceAudit: Array<{
    source: string
    action: string
    target?: string
    total: number
    expr: string
  }>
  createdCharacters: CreateCharacterInput[]
  fullMessages: ChatCompletionMessageParam[]
}

/**
 * Build system instructions for the GM
 */
function buildSystemInstructions(
  rulesContext: string,
  moduleContext: string,
  journal?: ParsedJournal | null,
  settings?: { ability_scores_4d6L?: boolean; level1_max_hp?: boolean }
): string {
  let homebrewRules = ''

  if (settings?.ability_scores_4d6L || settings?.level1_max_hp) {
    homebrewRules = '\n\nHOMEBREW RULES (apply these in addition to the standard rules):\n'
    if (settings.ability_scores_4d6L) {
      homebrewRules += '- **Ability scores**: Use 4d6 drop lowest (4d6L) for each ability score when creating new characters.\n'
    }
    if (settings.level1_max_hp) {
      homebrewRules += '- **Level 1 maximum HP**: All level 1 characters receive maximum hit points from their hit die (do not roll).\n'
    }
  }

  // Build journal context if available
  let journalContext = ''
  if (journal) {
    journalContext = '\n\n## JOURNAL CONTEXT (SAVED GAME STATE)\n'
    journalContext += 'The following information represents the current state of the adventure. You MUST use this context to understand where the party is, what they have done, and who the characters are.\n\n'

    // Add party information
    if (journal.frontMatter.party && journal.frontMatter.party.length > 0) {
      journalContext += '### PARTY:\n'
      journal.frontMatter.party.forEach((character) => {
        journalContext += `- **${character.name}** (${character.class}, Level ${character.level})\n`
        journalContext += `  - HP: ${character.hp}/${character.max_hp}\n`
        journalContext += `  - AC: ${character.ac}, THAC0: ${character.thac0 ?? 'N/A'}, XP: ${character.xp ?? 0}\n`
        journalContext += `  - Abilities: STR ${character.abilities.str}, INT ${character.abilities.int}, WIS ${character.abilities.wis}, DEX ${character.abilities.dex}, CON ${character.abilities.con}, CHA ${character.abilities.cha}\n`
        if (character.inventory && character.inventory.length > 0) {
          journalContext += `  - Inventory: ${character.inventory.join(', ')}\n`
        }
      })
      journalContext += '\n'
    }

    // Add session log
    if (journal.sessionLog && journal.sessionLog.length > 0) {
      journalContext += '### SESSION LOG (Previous events):\n'
      // Limit to last 10 entries to avoid token bloat, or all if fewer
      const recentLog = journal.sessionLog.slice(-10)
      recentLog.forEach((entry) => {
        journalContext += `${entry}\n`
      })
      journalContext += '\n'
    }

    // Add characters section (narrative descriptions)
    if (journal.characters && journal.characters.trim().length > 0) {
      journalContext += '### CHARACTER DETAILS:\n'
      journalContext += journal.characters.trim() + '\n\n'
    }

    // Add inventory section (party-wide inventory)
    if (journal.inventory && journal.inventory.trim().length > 0) {
      journalContext += '### PARTY INVENTORY:\n'
      journalContext += journal.inventory.trim() + '\n\n'
    }

    // Add house rules from journal
    if (journal.houseRules && journal.houseRules.trim().length > 0) {
      journalContext += '### HOUSE RULES (from journal):\n'
      journalContext += journal.houseRules.trim() + '\n\n'
    }
  }

  return `You are the Game Master for a B/X D&D-compatible tabletop RPG session.

CRITICAL RULES:
1. **Rule primacy**: You must ONLY use the rules and module provided. Never invent or assume rules from other systems.
2. **Refusal policy**: If a player attempts an action not supported by the uploaded rules, refuse politely and include a brief excerpt from the rules (max 256 characters) explaining why.
3. **Dice rolls**: ALL dice rolls MUST be performed using the roll_dice function tool. NEVER simulate, estimate, or make up dice results.
4. **Character creation**: When a player creates a new character, guide them through character creation according to the rules PDF, then MUST call the create_character tool to add the character to the party. Include all required stats (name, class, level, HP, abilities, AC, etc.).${homebrewRules}

RULES CONTEXT:
${rulesContext.substring(0, 4000)}

MODULE CONTEXT:
${moduleContext.substring(0, 4000)}
${journalContext}
Remember: Be faithful to the rules, use the dice tool for all rolls, and maintain the game's narrative consistency.`
}

/**
 * Execute tool calls locally
 */
function executeToolCall(name: string, argumentsJson: string): string {
  if (name === 'roll_dice') {
    try {
      const args = JSON.parse(argumentsJson)
      const validated = DiceRollInputSchema.parse(args)
      const result = rollDice_tool(validated)

      return JSON.stringify(result)
    } catch (error) {
      return JSON.stringify({
        error: 'Invalid dice roll parameters',
        details: error instanceof Error ? error.message : String(error),
      })
    }
  }

  if (name === 'create_character') {
    try {
      const args = JSON.parse(argumentsJson)
      const validated = CreateCharacterInputSchema.parse(args)

      // Return the validated character data
      return JSON.stringify({
        success: true,
        character: validated,
      })
    } catch (error) {
      return JSON.stringify({
        error: 'Invalid character parameters',
        details: error instanceof Error ? error.message : String(error),
      })
    }
  }

  return JSON.stringify({ error: `Unknown tool: ${name}` })
}

/**
 * Main orchestration function for GM responses
 * Handles tool calls via round-trip pattern with support for reasoning models
 * that may make multiple sequential tool calls
 */
export async function getGMResponse(request: GMRequest): Promise<GMResponse> {
  const { client, messages, rulesContext, moduleContext, journal, model = 'gpt-4o-2024-08-06', settings } = request

  const systemInstructions = buildSystemInstructions(rulesContext, moduleContext, journal, settings)

  // Build initial messages with system instructions
  const messagesWithSystem: ChatCompletionMessageParam[] = [
    { role: 'system', content: systemInstructions },
    ...messages,
  ]

  const diceAudit: GMResponse['diceAudit'] = []
  const createdCharacters: CreateCharacterInput[] = []
  let currentMessages = [...messagesWithSystem]

  // Maximum iterations to prevent infinite loops with reasoning models
  const MAX_ITERATIONS = 10
  let iterations = 0

  // Loop to handle multiple rounds of tool calls (for reasoning models)
  while (iterations < MAX_ITERATIONS) {
    iterations++

    // Determine which token parameter to use based on model
    // GPT-5 models require max_completion_tokens and don't support temperature
    // GPT-4 models use max_tokens and support temperature
    const isGPT5Model = model.toLowerCase().includes('gpt-5')
    const tokenParam = isGPT5Model ? 'max_completion_tokens' : 'max_tokens'

    // API call with tools enabled
    const response = await client.chat.completions.create({
      model,
      messages: currentMessages,
      tools: tools as OpenAI.Chat.Completions.ChatCompletionTool[],
      parallel_tool_calls: false, // Force sequential tool calls for determinism
      // GPT-5 models don't support temperature parameter
      ...(!isGPT5Model && settings?.temperature !== undefined && { temperature: settings.temperature }),
      ...(settings?.max_tokens !== undefined && { [tokenParam]: settings.max_tokens }),
    })

    const choice = response.choices[0]
    if (!choice) {
      throw new Error('No response from API')
    }

    // Add assistant's message to conversation history
    if (choice.message) {
      currentMessages.push(choice.message)
    }

    // Check for tool calls
    if (choice.message.tool_calls && choice.message.tool_calls.length > 0) {
      // Execute tool calls
      for (const toolCall of choice.message.tool_calls) {
        const result = executeToolCall(toolCall.function.name, toolCall.function.arguments)

        // Parse the result to add to dice audit or character list
        try {
          const resultObj = JSON.parse(result)
          const argsObj = JSON.parse(toolCall.function.arguments)

          if (!resultObj.error) {
            // Handle dice rolls
            if (toolCall.function.name === 'roll_dice') {
              diceAudit.push({
                source: argsObj.source || 'Unknown',
                action: argsObj.action || 'roll',
                target: argsObj.target,
                total: resultObj.total,
                expr: resultObj.normalized_expr || argsObj.expr,
              })
            }

            // Handle character creation
            if (toolCall.function.name === 'create_character' && resultObj.character) {
              createdCharacters.push(resultObj.character)
            }
          }
        } catch {
          // Ignore parse errors for audit
        }

        // Add tool result to messages
        currentMessages.push({
          role: 'tool',
          tool_call_id: toolCall.id,
          content: result,
        })
      }

      // Continue loop to let model process tool results and potentially make more calls
      continue
    }

    // No tool calls - we have a final response
    const text = choice.message.content || ''

    return {
      text,
      diceAudit,
      createdCharacters,
      fullMessages: currentMessages,
    }
  }

  // If we hit max iterations, return what we have
  const lastMessage = currentMessages[currentMessages.length - 1]
  const text = lastMessage && 'content' in lastMessage && lastMessage.content
    ? String(lastMessage.content)
    : 'Maximum iterations reached. Please try again.'

  return {
    text,
    diceAudit,
    createdCharacters,
    fullMessages: currentMessages,
  }
}

/**
 * Format dice audit for display
 */
export function formatDiceAudit(
  audit: GMResponse['diceAudit']
): string {
  if (audit.length === 0) {
    return ''
  }

  const lines = audit.map((roll) => {
    const target = roll.target ? ` ${roll.target}` : ''
    return `- ${roll.source} ${roll.action}${target}: ${roll.total} (${roll.expr})`
  })

  return '\n\n**Dice audit**\n' + lines.join('\n')
}
