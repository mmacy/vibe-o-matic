import type { GMResponse } from '@/lib/openai/orchestration'

/**
 * Determines if an interaction is significant enough to warrant a journal entry.
 * Only narrative-significant or critical events should be logged.
 */
export function isJournalWorthy(
  userMessage: string,
  response: GMResponse
): boolean {
  // Character creation is always journal-worthy
  if (response.createdCharacters && response.createdCharacters.length > 0) {
    return true
  }

  // Dice rolls indicate combat, skill checks, or other mechanically important events
  if (response.diceAudit && response.diceAudit.length > 0) {
    return true
  }

  // Long responses (>300 chars) likely contain important narrative
  if (response.text.length > 300) {
    return true
  }

  // Check for narrative keywords indicating significant events
  const significantKeywords = [
    // Discovery and exploration
    'discover', 'find', 'found', 'reveal', 'hidden', 'secret', 'treasure',
    // Combat and danger
    'attack', 'damage', 'kill', 'defeat', 'flee', 'escape', 'ambush', 'encounter',
    // Character state changes
    'level up', 'died', 'death', 'unconscious', 'poison', 'disease', 'curse',
    // Story progression
    'quest', 'mission', 'arrive', 'enter', 'reach', 'complete', 'finish',
    // Important NPCs and locations
    'meet', 'speak with', 'village', 'town', 'city', 'dungeon', 'cave',
    // Decisions and consequences
    'decide', 'choice', 'agree', 'refuse', 'accept', 'decline',
  ]

  const combinedText = (userMessage + ' ' + response.text).toLowerCase()
  const hasSignificantKeyword = significantKeywords.some(keyword =>
    combinedText.includes(keyword)
  )

  return hasSignificantKeyword
}

/**
 * Creates a narrative summary of an interaction for the journal.
 * Provides context and detail while remaining concise.
 */
export function createJournalEntry(
  userMessage: string,
  response: GMResponse
): string {
  const parts: string[] = []

  // Extract action from user message (first sentence or reasonable length)
  const userAction = extractPlayerAction(userMessage)

  // Extract outcome from GM response
  const outcome = extractOutcome(response)

  // Build the entry
  if (userAction && outcome) {
    parts.push(`${userAction} → ${outcome}`)
  } else if (userAction) {
    parts.push(userAction)
  } else if (outcome) {
    parts.push(outcome)
  }

  // Add dice roll summary if present (combat/checks are important)
  if (response.diceAudit && response.diceAudit.length > 0) {
    const dicesSummary = summarizeDiceRolls(response.diceAudit)
    if (dicesSummary) {
      parts.push(dicesSummary)
    }
  }

  // Add character creation note
  if (response.createdCharacters && response.createdCharacters.length > 0) {
    const names = response.createdCharacters.map(c => c.name).join(', ')
    parts.push(`[New character${response.createdCharacters.length > 1 ? 's' : ''}: ${names}]`)
  }

  return parts.join(' ')
}

/**
 * Extract the player's action from their message in a concise form.
 */
function extractPlayerAction(message: string): string {
  // Get first sentence or up to 200 characters
  const firstSentence = message.match(/^[^.!?]+[.!?]/)
  if (firstSentence) {
    return firstSentence[0].trim()
  }

  // If no sentence boundary, take first 200 chars with smart truncation
  if (message.length <= 200) {
    return message.trim()
  }

  // Find last complete word within 200 chars
  const truncated = message.substring(0, 200)
  const lastSpace = truncated.lastIndexOf(' ')
  if (lastSpace > 150) { // Only use word boundary if we're still getting good length
    return truncated.substring(0, lastSpace) + '...'
  }

  return truncated + '...'
}

/**
 * Extract the key outcome from the GM's response.
 */
function extractOutcome(response: GMResponse): string {
  const text = response.text

  // Get first sentence or first paragraph (up to 250 chars)
  const firstParagraph = text.split('\n\n')[0]
  const firstSentence = firstParagraph.match(/^[^.!?]+[.!?]/)

  if (firstSentence) {
    const sentence = firstSentence[0].trim()
    if (sentence.length <= 250) {
      return sentence
    }
  }

  // If no good sentence, use smart truncation
  if (firstParagraph.length <= 250) {
    return firstParagraph.trim()
  }

  const truncated = firstParagraph.substring(0, 250)
  const lastSpace = truncated.lastIndexOf(' ')
  if (lastSpace > 200) {
    return truncated.substring(0, lastSpace) + '...'
  }

  return truncated + '...'
}

/**
 * Summarize dice rolls into a readable format.
 */
function summarizeDiceRolls(audit: GMResponse['diceAudit']): string {
  if (audit.length === 0) return ''

  // Group by source for cleaner output
  const rollsBySource = new Map<string, typeof audit>()
  for (const roll of audit) {
    const source = roll.source || 'Unknown'
    if (!rollsBySource.has(source)) {
      rollsBySource.set(source, [])
    }
    rollsBySource.get(source)!.push(roll)
  }

  const summaries: string[] = []
  for (const [source, rolls] of rollsBySource) {
    if (rolls.length === 1) {
      const r = rolls[0]
      const target = r.target ? ` vs ${r.target}` : ''
      summaries.push(`${source} ${r.action}${target}: ${r.total}`)
    } else {
      // Multiple rolls from same source
      const actions = rolls.map(r => {
        const target = r.target ? ` vs ${r.target}` : ''
        return `${r.action}${target}(${r.total})`
      }).join(', ')
      summaries.push(`${source}: ${actions}`)
    }
  }

  return `[${summaries.join('; ')}]`
}
