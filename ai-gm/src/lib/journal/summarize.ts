import OpenAI from 'openai'
import type { JournalEntryCache } from '@/app/state/schema'

/**
 * Formats cached journal entries for AI summarization
 */
function formatCacheForSummarization(cache: JournalEntryCache[]): string {
  if (cache.length === 0) {
    return 'No interactions to summarize.'
  }

  const lines: string[] = []

  cache.forEach((entry, index) => {
    lines.push(`\n--- Interaction ${index + 1} ---`)
    lines.push(`Timestamp: ${new Date(entry.timestamp).toLocaleString()}`)
    lines.push(`\nPlayer: ${entry.userMessage}`)
    lines.push(`\nGM: ${entry.gmResponse}`)

    if (entry.diceAudit && entry.diceAudit.length > 0) {
      lines.push('\nDice Rolls:')
      entry.diceAudit.forEach((roll) => {
        const target = roll.target ? ` vs ${roll.target}` : ''
        lines.push(`  - ${roll.source} ${roll.action}${target}: ${roll.total} (${roll.expr})`)
      })
    }

    if (entry.createdCharacters && entry.createdCharacters.length > 0) {
      lines.push('\nCharacters Created:')
      entry.createdCharacters.forEach((char) => {
        lines.push(`  - ${char.name} (${char.class}, Level ${char.level})`)
      })
    }
  })

  return lines.join('\n')
}

/**
 * Sends cached journal entries to AI for narrative summarization
 */
export async function summarizeJournalCache(
  client: OpenAI,
  cache: JournalEntryCache[],
  model: string = 'gpt-4o-2024-08-06'
): Promise<string> {
  if (cache.length === 0) {
    throw new Error('Cannot summarize empty cache')
  }

  const formattedCache = formatCacheForSummarization(cache)

  const systemPrompt = `You are a skilled Game Master assistant helping to maintain a campaign journal.

Your task is to read a series of game interactions and create a brief, impactful journal entry that captures the important events, decisions, and outcomes.

TONE & STYLE:
- Write like a succinct Gandalf: wise, measured, and direct
- Favor brevity and impact over elaborate descriptions
- Avoid flowery language, excessive adjectives, and dramatic flourishes
- Use clear, straightforward prose that conveys meaning efficiently

GUIDELINES:
- Write in past tense, third person perspective
- Focus on key events: combat outcomes, discoveries, major decisions, character moments
- Include essential details: character names, locations, outcomes
- Mention dice rolls only when critical to understanding what happened
- Keep the summary brief and impactful (aim for 1-3 short paragraphs)
- If characters were created, note their names and classes
- Preserve chronological flow
- Skip trivial interactions, clarifications, and minor descriptions

FORMAT:
Return ONLY the journal entry text. Do not include any preamble, metadata, or commentary about the task.`

  const userPrompt = `Please summarize the following game session interactions into a brief journal entry:

${formattedCache}

Remember: Be concise and impactful. Focus on what actually happened. Write like a wise chronicler recording essential facts, not a novelist embellishing a tale.`

  // Determine which token parameter to use based on model
  // GPT-5 models require max_completion_tokens and don't support temperature
  // GPT-4 models use max_tokens and support temperature
  const isGPT5Model = model.toLowerCase().includes('gpt-5')
  const tokenParam = isGPT5Model ? 'max_completion_tokens' : 'max_tokens'

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    // GPT-5 models don't support temperature parameter
    ...(!isGPT5Model ? { temperature: 0.5 } : {}), // More controlled for concise, factual output
    [tokenParam]: 600, // Enforces brevity
  })

  // Extract content from response
  const choice = response.choices?.[0]
  if (!choice) {
    throw new Error(`No choices in API response. Response: ${JSON.stringify(response)}`)
  }

  const summary = choice.message?.content
  if (!summary) {
    // GPT-5 models may refuse or have empty content
    const refusal = choice.message?.refusal
    if (refusal) {
      throw new Error(`Model refused to generate summary: ${refusal}`)
    }
    throw new Error(`No content in response message. Choice: ${JSON.stringify(choice)}`)
  }

  return summary.trim()
}
