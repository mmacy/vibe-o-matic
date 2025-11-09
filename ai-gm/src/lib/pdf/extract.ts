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
 * Pattern looks for lines containing AC, HD, HP, etc.
 */
function extractStatBlocks(text: string): StatBlock[] {
  const blocks: StatBlock[] = []
  const lines = text.split(/\n+/)

  // Look for stat block patterns
  // Typical format: "AC X, HD Y, HP Z, MV A, Att B, Dmg C, Save D, Morale E, XP F"
  const statBlockRegex =
    /AC\s*[:\s]*([^,]+),?\s*HD\s*[:\s]*([^,]+),?\s*HP\s*[:\s]*([^,]+)/i

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]
    const match = line.match(statBlockRegex)

    if (match) {
      // Found a potential stat block
      // Try to extract creature name from previous line
      const name = i > 0 ? lines[i - 1].trim() : 'Unknown'

      // Parse all stat components
      const ac = extractField(line, 'AC') || match[1].trim()
      const hd = extractField(line, 'HD') || match[2].trim()
      const hp = extractField(line, 'HP') || match[3].trim()
      const mv = extractField(line, 'MV') || extractField(line, 'Move') || ''
      const att = extractField(line, 'Att') || extractField(line, 'Attack') || ''
      const dmg = extractField(line, 'Dmg') || extractField(line, 'Damage') || ''
      const save = extractField(line, 'Save') || extractField(line, 'Sv') || ''
      const morale = extractField(line, 'Morale') || extractField(line, 'ML') || ''
      const xp = extractField(line, 'XP') || ''

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
        text: line,
      })
    }
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
