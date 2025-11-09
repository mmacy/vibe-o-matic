import OpenAI from 'openai'

/**
 * Create OpenAI client with user-provided API key
 */
export function createClient(apiKey: string): OpenAI {
  return new OpenAI({
    apiKey,
    dangerouslyAllowBrowser: true, // Client-only app, BYOK
  })
}

/**
 * Aggregate text output from response items
 * The Responses API output is heterogeneous, so we need to iterate items
 */
export function aggregateOutputText(output: unknown[]): string {
  const textParts: string[] = []

  for (const item of output) {
    if (typeof item === 'object' && item !== null) {
      const obj = item as Record<string, unknown>

      // Check for text content
      if (obj.type === 'text' && typeof obj.text === 'string') {
        textParts.push(obj.text)
      }
      // Handle content blocks that might have text
      else if (obj.content && typeof obj.content === 'string') {
        textParts.push(obj.content)
      }
    }
  }

  return textParts.join('\n\n').trim()
}

/**
 * Extract tool calls from response output
 */
export function extractToolCalls(output: unknown[]): Array<{
  id: string
  name: string
  arguments: string
}> {
  const toolCalls: Array<{ id: string; name: string; arguments: string }> = []

  for (const item of output) {
    if (typeof item === 'object' && item !== null) {
      const obj = item as Record<string, unknown>

      if (obj.type === 'function_call' || obj.type === 'tool_call') {
        const toolCall = {
          id: typeof obj.id === 'string' ? obj.id : `call_${Date.now()}`,
          name: '',
          arguments: '',
        }

        // Extract function name
        if (typeof obj.name === 'string') {
          toolCall.name = obj.name
        } else if (typeof obj.function === 'object' && obj.function !== null) {
          const func = obj.function as Record<string, unknown>
          if (typeof func.name === 'string') {
            toolCall.name = func.name
          }
          if (typeof func.arguments === 'string') {
            toolCall.arguments = func.arguments
          }
        }

        // Extract arguments
        if (typeof obj.arguments === 'string' && !toolCall.arguments) {
          toolCall.arguments = obj.arguments
        }

        if (toolCall.name) {
          toolCalls.push(toolCall)
        }
      }
    }
  }

  return toolCalls
}
