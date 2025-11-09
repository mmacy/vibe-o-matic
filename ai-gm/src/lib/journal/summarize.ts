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

Your task is to read a series of game interactions and create a concise, narrative journal entry that captures the important events, decisions, and outcomes.

GUIDELINES:
- Write in past tense, third person perspective
- Focus on narrative-significant events (combat, discoveries, major decisions, character moments)
- Include specific details like character names, locations, and outcomes
- Mention dice rolls only when they're critical to understanding what happened
- Keep the summary concise but informative (aim for 2-4 paragraphs)
- If characters were created, note their names and classes
- Preserve the chronological flow of events
- Skip trivial interactions like asking for clarification or basic descriptions

FORMAT:
Return ONLY the journal entry text. Do not include any preamble, metadata, or commentary about the task.`

  const userPrompt = `Please summarize the following game session interactions into a narrative journal entry:

${formattedCache}

Remember: Focus on what actually happened in the story. Create a journal entry that would help the GM and players remember this session and could help an AI GM continue the adventure later.`

  const response = await client.chat.completions.create({
    model,
    messages: [
      { role: 'system', content: systemPrompt },
      { role: 'user', content: userPrompt },
    ],
    temperature: 0.7, // Slightly creative but mostly factual
    max_tokens: 1000, // Reasonable length for a journal entry
  })

  const summary = response.choices[0]?.message?.content
  if (!summary) {
    throw new Error('Failed to generate journal summary')
  }

  return summary.trim()
}
