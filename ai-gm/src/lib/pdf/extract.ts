import * as pdfjsLib from 'pdfjs-dist'

// Set worker source for pdf.js
pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.min.mjs`

export interface ExtractedText {
  text: string
  pageNumber: number
}

export interface ParsedDocument {
  title: string
  pages: ExtractedText[]
  fullText: string
  statBlocks: StatBlock[]
}

export interface StatBlock {
  name: string
  ac: string
  hd: string
  hp: string
  mv: string
  att: string
  dmg: string
  save: string
  morale: string
  xp: string
  text: string
}

/**
 * Extract text from a PDF file
 */
export async function extractTextFromPDF(file: File): Promise<ParsedDocument> {
  const arrayBuffer = await file.arrayBuffer()
  const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise

  const pages: ExtractedText[] = []
  const statBlocks: StatBlock[] = []

  for (let i = 1; i <= pdf.numPages; i++) {
    const page = await pdf.getPage(i)
    const textContent = await page.getTextContent()

    const pageText = textContent.items
      .map((item) => {
        if ('str' in item) {
          return item.str
        }
        return ''
      })
      .join(' ')

    pages.push({
      text: pageText,
      pageNumber: i,
    })

    // Try to extract stat blocks from this page
    const foundStatBlocks = extractStatBlocks(pageText)
    statBlocks.push(...foundStatBlocks)
  }

  const fullText = pages.map((p) => p.text).join('\n\n')

  return {
    title: file.name.replace('.pdf', ''),
    pages,
    fullText,
    statBlocks,
  }
}

/**
 * Extract OSE/B/X style stat blocks from text
 * Uses global regex to find all occurrences in the text
 */
function extractStatBlocks(text: string): StatBlock[] {
  const blocks: StatBlock[] = []

  // Look for stat block patterns with global flag
  // Typical format: "AC X, HD Y, HP Z, MV A, Att B, Dmg C, Save D, Morale E, XP F"
  // Capture context before the stat block to extract the creature name
  const statBlockRegex =
    /([A-Z][A-Za-z\s'-]+?)\s+AC\s*[:\s]*([^,]+),?\s*HD\s*[:\s]*([^,]+),?\s*HP\s*[:\s]*([^,]+)[^.]*?(?=(?:[A-Z][A-Za-z\s'-]+?\s+AC|$))/gi

  const matches = text.matchAll(statBlockRegex)

  for (const match of matches) {
    const fullMatch = match[0]
    const name = match[1].trim()
    const ac = match[2].trim()
    const hd = match[3].trim()
    const hp = match[4].trim()

    // Extract additional fields from the full match
    const mv = extractField(fullMatch, 'MV') || extractField(fullMatch, 'Move') || ''
    const att = extractField(fullMatch, 'Att') || extractField(fullMatch, 'Attack') || ''
    const dmg = extractField(fullMatch, 'Dmg') || extractField(fullMatch, 'Damage') || ''
    const save = extractField(fullMatch, 'Save') || extractField(fullMatch, 'Sv') || ''
    const morale = extractField(fullMatch, 'Morale') || extractField(fullMatch, 'ML') || ''
    const xp = extractField(fullMatch, 'XP') || ''

    blocks.push({
      name,
      ac,
      hd,
      hp,
      mv,
      att,
      dmg,
      save,
      morale,
      xp,
      text: fullMatch,
    })
  }

  return blocks
}

/**
 * Extract a specific field from a stat block line
 */
function extractField(line: string, fieldName: string): string {
  const regex = new RegExp(`${fieldName}\\s*[:\\s]*([^,]+)`, 'i')
  const match = line.match(regex)
  return match ? match[1].trim() : ''
}

/**
 * Format stat blocks for LLM consumption
 */
export function formatStatBlocksForLLM(blocks: StatBlock[]): string {
  return blocks
    .map((block) => {
      return `**${block.name}**
AC ${block.ac}, HD ${block.hd}, HP ${block.hp}${block.mv ? `, MV ${block.mv}` : ''}${block.att ? `, Att ${block.att}` : ''}${block.dmg ? `, Dmg ${block.dmg}` : ''}${block.save ? `, Save ${block.save}` : ''}${block.morale ? `, Morale ${block.morale}` : ''}${block.xp ? `, XP ${block.xp}` : ''}`
    })
    .join('\n\n')
}
