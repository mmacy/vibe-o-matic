/**
 * Extract rule excerpts with maximum character limit
 */

const MAX_EXCERPT_LENGTH = 256

/**
 * Find relevant rule excerpt based on keywords
 */
export function findRuleExcerpt(rulesText: string, keywords: string[]): string {
  const lines = rulesText.split('\n')

  // Find lines containing any of the keywords
  const relevantLines: string[] = []

  for (const line of lines) {
    const lowerLine = line.toLowerCase()
    if (keywords.some((keyword) => lowerLine.includes(keyword.toLowerCase()))) {
      relevantLines.push(line.trim())
      if (relevantLines.join(' ').length > MAX_EXCERPT_LENGTH * 2) {
        break // Found enough context
      }
    }
  }

  if (relevantLines.length === 0) {
    return 'No matching rule found in uploaded materials.'
  }

  // Combine and trim to max length
  let excerpt = relevantLines.join(' ')

  if (excerpt.length > MAX_EXCERPT_LENGTH) {
    excerpt = excerpt.substring(0, MAX_EXCERPT_LENGTH - 3) + '...'
  }

  return excerpt
}

/**
 * Extract excerpt from specific section
 */
export function extractExcerptFromSection(text: string, sectionName: string): string {
  const lines = text.split('\n')
  let inSection = false
  const sectionLines: string[] = []

  for (const line of lines) {
    const trimmed = line.trim()

    // Check if we've found the section header
    if (trimmed.toLowerCase().includes(sectionName.toLowerCase())) {
      inSection = true
      sectionLines.push(trimmed)
      continue
    }

    // If we're in the section, collect lines
    if (inSection) {
      // Stop at next major header (all caps or starting with #)
      if (trimmed.match(/^[A-Z\s]{3,}$/) || trimmed.startsWith('#')) {
        break
      }
      sectionLines.push(trimmed)

      // Stop if we have enough
      if (sectionLines.join(' ').length > MAX_EXCERPT_LENGTH * 2) {
        break
      }
    }
  }

  if (sectionLines.length === 0) {
    return `Section "${sectionName}" not found.`
  }

  let excerpt = sectionLines.join(' ')

  if (excerpt.length > MAX_EXCERPT_LENGTH) {
    excerpt = excerpt.substring(0, MAX_EXCERPT_LENGTH - 3) + '...'
  }

  return excerpt
}

/**
 * Trim any text to max excerpt length
 */
export function trimToMaxLength(text: string): string {
  if (text.length <= MAX_EXCERPT_LENGTH) {
    return text
  }
  return text.substring(0, MAX_EXCERPT_LENGTH - 3) + '...'
}
