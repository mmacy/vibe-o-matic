import * as yaml from 'js-yaml'
import { JournalFrontMatterSchema, type JournalFrontMatter } from '@/app/state/schema'

export interface ParsedJournal {
  frontMatter: JournalFrontMatter
  sessionLog: string[]
  characters: string
  inventory: string
  houseRules: string
}

/**
 * Parse a journal markdown file with YAML front-matter
 */
export function parseJournal(markdown: string): ParsedJournal {
  // Extract YAML front-matter
  const frontMatterMatch = markdown.match(/^---\n([\s\S]*?)\n---/)

  if (!frontMatterMatch) {
    throw new Error('No YAML front-matter found in journal')
  }

  const frontMatterYaml = frontMatterMatch[1]
  const frontMatterRaw = yaml.load(frontMatterYaml)

  // Validate with Zod
  const frontMatter = JournalFrontMatterSchema.parse(frontMatterRaw)

  // Extract content after front-matter
  const content = markdown.substring(frontMatterMatch[0].length).trim()

  // Parse sections
  const sessionLog = extractSection(content, 'Session log') || []
  const characters = extractSection(content, 'Characters') || ''
  const inventory = extractSection(content, 'Inventory') || ''
  const houseRules = extractSection(content, 'House rules') || ''

  return {
    frontMatter,
    sessionLog: Array.isArray(sessionLog) ? sessionLog : sessionLog.split('\n').filter(Boolean),
    characters: typeof characters === 'string' ? characters : '',
    inventory: typeof inventory === 'string' ? inventory : '',
    houseRules: typeof houseRules === 'string' ? houseRules : '',
  }
}

/**
 * Extract a section from markdown content
 */
function extractSection(content: string, sectionName: string): string | string[] {
  const sectionRegex = new RegExp(`# ${sectionName}\\s*\\n([\\s\\S]*?)(?=\\n# |$)`, 'i')
  const match = content.match(sectionRegex)

  if (!match) {
    return ''
  }

  const sectionContent = match[1].trim()

  // For session log, return as array of lines
  if (sectionName.toLowerCase() === 'session log') {
    return sectionContent.split('\n').filter((line) => line.trim())
  }

  return sectionContent
}

/**
 * Create default journal from scratch
 */
export function createDefaultJournal(
  system: 'BX' | 'OSE',
  settings: { ability_scores_4d6L: boolean; level1_max_hp: boolean }
): ParsedJournal {
  const now = new Date().toISOString()

  const frontMatter: JournalFrontMatter = {
    schema_version: '1.0',
    system,
    party: [],
    flags: {
      ability_scores_4d6L: settings.ability_scores_4d6L,
      level1_max_hp: settings.level1_max_hp,
    },
    created_at: now,
    updated_at: now,
  }

  return {
    frontMatter,
    sessionLog: [],
    characters: '',
    inventory: '',
    houseRules: '',
  }
}
