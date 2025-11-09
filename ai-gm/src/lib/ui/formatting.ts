/**
 * Convert text to sentence case
 */
export function toSentenceCase(text: string): string {
  if (!text) return ''
  return text.charAt(0).toUpperCase() + text.slice(1).toLowerCase()
}

/**
 * Format label text for UI (sentence case)
 */
export function formatLabel(text: string): string {
  // Replace underscores and hyphens with spaces
  const cleaned = text.replace(/[_-]/g, ' ')

  // Convert to sentence case
  return toSentenceCase(cleaned)
}

/**
 * Format timestamp for display
 */
export function formatTimestamp(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleString()
}

/**
 * Format date only
 */
export function formatDate(isoString: string): string {
  const date = new Date(isoString)
  return date.toLocaleDateString()
}

/**
 * Truncate text with ellipsis
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) {
    return text
  }
  return text.substring(0, maxLength - 3) + '...'
}
