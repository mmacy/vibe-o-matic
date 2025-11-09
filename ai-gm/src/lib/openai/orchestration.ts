import OpenAI from 'openai'
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions'
import { rollDice_tool } from '@/lib/dice/roll'
import { DiceRollInputSchema, CreateCharacterInputSchema } from '@/app/state/schema'
import type { CreateCharacterInput } from '@/app/state/schema'
import { tools } from './tools'

export interface GMRequest {
  client: OpenAI
  messages: ChatCompletionMessageParam[]
  rulesContext: string
  moduleContext: string
  model?: string
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
function buildSystemInstructions(rulesContext: string, moduleContext: string): string {
  return `You are the Game Master for a B/X D&D-compatible tabletop RPG session.

CRITICAL RULES:
1. **Rule primacy**: You must ONLY use the rules and module provided. Never invent or assume rules from other systems.
2. **Refusal policy**: If a player attempts an action not supported by the uploaded rules, refuse politely and include a brief excerpt from the rules (max 256 characters) explaining why.
3. **Dice rolls**: ALL dice rolls MUST be performed using the roll_dice function tool. NEVER simulate, estimate, or make up dice results.
4. **Character creation**: When a player creates a new character, guide them through character creation according to the rules PDF, then MUST call the create_character tool to add the character to the party. Include all required stats (name, class, level, HP, abilities, AC, etc.).
5. **Response format**: After your narrative, include a "**Dice audit**" section listing all rolls as an unordered list with the format:
   - SOURCE ACTION TARGET: TOTAL (NdM+/-K)
   Omit TARGET when there is none.
   Example: "- Fighter attack Goblin: 17 (1d20+4)"
6. **Journal**: Keep track of the session. After each significant turn, note what happened in a single line for the session log.

RULES CONTEXT:
${rulesContext.substring(0, 4000)}

MODULE CONTEXT:
${moduleContext.substring(0, 4000)}

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
  const { client, messages, rulesContext, moduleContext, model = 'gpt-4o-2024-08-06' } = request

  const systemInstructions = buildSystemInstructions(rulesContext, moduleContext)

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

    // API call with tools enabled
    const response = await client.chat.completions.create({
      model,
      messages: currentMessages,
      tools: tools as OpenAI.Chat.Completions.ChatCompletionTool[],
      parallel_tool_calls: false, // Force sequential tool calls for determinism
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
