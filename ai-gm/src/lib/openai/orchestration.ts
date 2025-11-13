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
    ascending_ac?: boolean
    temperature?: number
    max_tokens?: number
  }
  onStreamChunk?: (chunk: string) => void
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
  settings?: { ability_scores_4d6L?: boolean; level1_max_hp?: boolean; ascending_ac?: boolean }
): string {
  let homebrewRules = ''

  if (settings?.ability_scores_4d6L || settings?.level1_max_hp || settings?.ascending_ac) {
    homebrewRules = '\n\nHOMEBREW RULES (apply these in addition to the standard rules):\n'
    if (settings.ability_scores_4d6L) {
      homebrewRules += '- **Ability scores**: Use 4d6 drop lowest (4d6L) for each ability score when creating new characters.\n'
    }
    if (settings.level1_max_hp) {
      homebrewRules += '- **Level 1 maximum HP**: All level 1 characters receive maximum hit points from their hit die (do not roll).\n'
    }
    if (settings.ascending_ac) {
      homebrewRules += '- **Ascending Armor Class**: Use ascending armor class where higher AC is better (instead of descending AC where lower is better).\n'
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
 * Supports streaming responses when onStreamChunk callback is provided
 */
export async function getGMResponse(request: GMRequest): Promise<GMResponse> {
  const { client, messages, rulesContext, moduleContext, journal, model = 'gpt-4o-2024-08-06', settings, onStreamChunk } = request

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

    // Determine which API to use based on model
    // GPT-5 models use Responses API for extended reasoning capabilities
    // GPT-4 models use Chat Completions API
    const isGPT5Model = model.toLowerCase().includes('gpt-5')

    // For GPT-5 models, use the Responses API
    if (isGPT5Model) {
      // Format messages as a single string input for the Responses API
      // The Responses API accepts a string or array of specific input items
      // For simplicity with tool calls and conversation history, we format as a string
      const formattedInput = currentMessages
        .map((msg) => {
          if (msg.role === 'system') {
            return `System: ${typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}`
          }
          if (msg.role === 'user') {
            return `User: ${typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}`
          }
          if (msg.role === 'assistant') {
            let text = `Assistant: ${typeof msg.content === 'string' ? msg.content : ''}`
            if ('tool_calls' in msg && msg.tool_calls) {
              text += `\n[Tool calls: ${JSON.stringify(msg.tool_calls)}]`
            }
            return text
          }
          if (msg.role === 'tool') {
            const toolMsg = msg as { tool_call_id: string; content: string | null }
            return `Tool result (${toolMsg.tool_call_id}): ${toolMsg.content}`
          }
          return ''
        })
        .filter((m) => m)
        .join('\n\n')

      const response = await client.responses.create({
        model,
        input: formattedInput,
        // TypeScript types expect flat structure, but runtime API requires nested structure with 'function' property
        tools: tools.map((tool) => ({
          type: 'function' as const,
          function: {
            name: tool.function.name,
            ...(tool.function.description && { description: tool.function.description }),
            parameters: tool.function.parameters || {},
            ...(tool.function.strict !== undefined && tool.function.strict !== null && { strict: tool.function.strict }),
          },
        })) as any,
        ...(settings?.max_tokens !== undefined && { max_output_tokens: settings.max_tokens }),
        reasoning: {
          effort: 'medium', // Use medium effort for GM responses
        },
        parallel_tool_calls: false, // Force sequential tool calls for determinism
        // Responses API supports streaming
        stream: !!onStreamChunk,
      })

      // Handle Responses API streaming
      if (onStreamChunk && Symbol.asyncIterator in response) {
        let accumulatedText = ''
        const accumulatedToolCalls: Array<{
          id: string
          type: 'function'
          function: { name: string; arguments: string }
        }> = []

        for await (const event of response) {
          // Handle text deltas
          if ((event as any).type === 'response.output_text.delta') {
            const delta = (event as any).delta
            if (delta) {
              accumulatedText += delta
              onStreamChunk(delta)
            }
          }
          // Handle complete output items
          if ((event as any).type === 'response.output_item.done') {
            const item = (event as any).item
            if (item?.type === 'text') {
              // Text already accumulated via deltas
            }
            // Handle tool calls
            if (item?.type === 'function_call') {
              accumulatedToolCalls.push({
                id: item.id || `call_${Date.now()}`,
                type: 'function',
                function: {
                  name: item.name || '',
                  arguments: item.arguments || '',
                },
              })
            }
          }
        }

        // Build assistant message for conversation history
        const assistantMessage: ChatCompletionMessageParam = {
          role: 'assistant',
          content: accumulatedText || null,
        }
        if (accumulatedToolCalls.length > 0) {
          assistantMessage.tool_calls = accumulatedToolCalls
        }
        currentMessages.push(assistantMessage)

        // Execute tool calls if present
        if (accumulatedToolCalls.length > 0) {
          for (const toolCall of accumulatedToolCalls) {
            const result = executeToolCall(toolCall.function.name, toolCall.function.arguments)

            // Parse the result for audit
            try {
              const resultObj = JSON.parse(result)
              const argsObj = JSON.parse(toolCall.function.arguments)

              if (!resultObj.error) {
                if (toolCall.function.name === 'roll_dice') {
                  diceAudit.push({
                    source: argsObj.source || 'Unknown',
                    action: argsObj.action || 'roll',
                    target: argsObj.target,
                    total: resultObj.total,
                    expr: resultObj.normalized_expr || argsObj.expr,
                  })
                }
                if (toolCall.function.name === 'create_character' && resultObj.character) {
                  createdCharacters.push(resultObj.character)
                }
              }
            } catch {
              // Ignore parse errors
            }

            // Add tool result to messages
            currentMessages.push({
              role: 'tool',
              tool_call_id: toolCall.id,
              content: result,
            })
          }

          // Continue loop for more tool calls
          continue
        }

        // No tool calls - return final response
        return {
          text: accumulatedText,
          diceAudit,
          createdCharacters,
          fullMessages: currentMessages,
        }
      }

      // Non-streaming Responses API
      if (Symbol.asyncIterator in response) {
        throw new Error('Expected non-streaming response but got streaming response')
      }

      const output = (response as any).output || []
      let text = (response as any).output_text || ''
      const toolCalls: Array<{
        id: string
        type: 'function'
        function: { name: string; arguments: string }
      }> = []

      // Parse output items
      for (const item of output) {
        if (item.type === 'text' && item.text) {
          if (!text) text = item.text
        }
        if (item.type === 'function_call') {
          toolCalls.push({
            id: item.id || `call_${Date.now()}`,
            type: 'function',
            function: {
              name: item.name || '',
              arguments: item.arguments || '',
            },
          })
        }
      }

      // Add assistant message to history
      const assistantMessage: ChatCompletionMessageParam = {
        role: 'assistant',
        content: text || null,
      }
      if (toolCalls.length > 0) {
        assistantMessage.tool_calls = toolCalls
      }
      currentMessages.push(assistantMessage)

      // Execute tool calls if present
      if (toolCalls.length > 0) {
        for (const toolCall of toolCalls) {
          const result = executeToolCall(toolCall.function.name, toolCall.function.arguments)

          // Parse the result for audit
          try {
            const resultObj = JSON.parse(result)
            const argsObj = JSON.parse(toolCall.function.arguments)

            if (!resultObj.error) {
              if (toolCall.function.name === 'roll_dice') {
                diceAudit.push({
                  source: argsObj.source || 'Unknown',
                  action: argsObj.action || 'roll',
                  target: argsObj.target,
                  total: resultObj.total,
                  expr: resultObj.normalized_expr || argsObj.expr,
                })
              }
              if (toolCall.function.name === 'create_character' && resultObj.character) {
                createdCharacters.push(resultObj.character)
              }
            }
          } catch {
            // Ignore parse errors
          }

          // Add tool result to messages
          currentMessages.push({
            role: 'tool',
            tool_call_id: toolCall.id,
            content: result,
          })
        }

        // Continue loop for more tool calls
        continue
      }

      // No tool calls - return final response
      return {
        text,
        diceAudit,
        createdCharacters,
        fullMessages: currentMessages,
      }
    }

    // For GPT-4 models, use the Chat Completions API (existing code)
    const tokenParam = 'max_tokens'

    // API call with tools enabled and optional streaming
    const response = await client.chat.completions.create({
      model,
      messages: currentMessages,
      tools: tools as OpenAI.Chat.Completions.ChatCompletionTool[],
      parallel_tool_calls: false, // Force sequential tool calls for determinism
      ...(settings?.temperature !== undefined && { temperature: settings.temperature }),
      ...(settings?.max_tokens !== undefined && { [tokenParam]: settings.max_tokens }),
      // Enable streaming if callback is provided
      stream: !!onStreamChunk,
    })

    // Handle streaming response
    if (onStreamChunk && Symbol.asyncIterator in response) {
      let accumulatedContent = ''
      let accumulatedToolCalls: Array<{
        id: string
        type: 'function'
        function: {
          name: string
          arguments: string
        }
      }> = []

      for await (const chunk of response) {
        const delta = chunk.choices[0]?.delta

        if (!delta) continue

        // Handle content streaming
        if (delta.content) {
          accumulatedContent += delta.content
          onStreamChunk(delta.content)
        }

        // Handle tool calls in streaming mode
        if (delta.tool_calls) {
          for (const toolCall of delta.tool_calls) {
            const index = toolCall.index

            // Initialize tool call if needed
            if (!accumulatedToolCalls[index]) {
              accumulatedToolCalls[index] = {
                id: toolCall.id || '',
                type: 'function',
                function: {
                  name: toolCall.function?.name || '',
                  arguments: '',
                },
              }
            }

            // Accumulate function arguments
            if (toolCall.function?.arguments) {
              accumulatedToolCalls[index].function.arguments += toolCall.function.arguments
            }

            // Update function name if provided
            if (toolCall.function?.name) {
              accumulatedToolCalls[index].function.name = toolCall.function.name
            }

            // Update tool call ID if provided
            if (toolCall.id) {
              accumulatedToolCalls[index].id = toolCall.id
            }
          }
        }
      }

      // Add assistant's message to conversation history
      const assistantMessage: ChatCompletionMessageParam = {
        role: 'assistant',
        content: accumulatedContent || null,
      }

      // Add tool calls if present
      if (accumulatedToolCalls.length > 0) {
        assistantMessage.tool_calls = accumulatedToolCalls
      }

      currentMessages.push(assistantMessage)

      // Check for tool calls
      if (accumulatedToolCalls.length > 0) {
        // Execute tool calls
        for (const toolCall of accumulatedToolCalls) {
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
      return {
        text: accumulatedContent,
        diceAudit,
        createdCharacters,
        fullMessages: currentMessages,
      }
    }

    // Non-streaming response (original behavior)
    // Type guard: if we reach here and it's still an async iterator, something went wrong
    if (Symbol.asyncIterator in response) {
      throw new Error('Expected non-streaming response but got streaming response')
    }

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
