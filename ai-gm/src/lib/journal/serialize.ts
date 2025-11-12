import * as yaml from 'js-yaml'
import type { ParsedJournal } from './parse'
import type { JournalFrontMatter } from '@/app/state/schema'

/**
 * Serialize journal to markdown with YAML front-matter
 */
export function serializeJournal(journal: ParsedJournal): string {
  const frontMatterYaml = yaml.dump(journal.frontMatter, {
    indent: 2,
    lineWidth: -1,
    noRefs: true,
  })

  const sections: string[] = []

  // Front-matter
  sections.push('---')
  sections.push(frontMatterYaml.trim())
  sections.push('---')
  sections.push('')

  // Session log
  sections.push('# Session log')
  sections.push('')
  if (journal.sessionLog.length > 0) {
    sections.push(...journal.sessionLog)
  } else {
    sections.push('_No entries yet_')
  }
  sections.push('')

  // Characters
  sections.push('# Characters')
  sections.push('')
  if (journal.characters) {
    sections.push(journal.characters)
  } else if (journal.frontMatter.party.length > 0) {
    // Generate character list from party
    journal.frontMatter.party.forEach((char) => {
      sections.push(`## ${char.name}`)
      sections.push(`- Class: ${char.class}`)
      sections.push(`- Level: ${char.level}`)
      sections.push(`- HP: ${char.hp}/${char.max_hp}`)
      sections.push(`- AC: ${char.ac}`)
      sections.push(`- Abilities: STR ${char.abilities.str}, INT ${char.abilities.int}, WIS ${char.abilities.wis}, DEX ${char.abilities.dex}, CON ${char.abilities.con}, CHA ${char.abilities.cha}`)
      sections.push(`- XP: ${char.xp}`)
      sections.push('')
    })
  } else {
    sections.push('_No characters yet_')
  }
  sections.push('')

  // Inventory
  sections.push('# Inventory')
  sections.push('')
  if (journal.inventory) {
    sections.push(journal.inventory)
  } else {
    sections.push('_No items yet_')
  }
  sections.push('')

  // House rules
  sections.push('# House rules')
  sections.push('')
  if (journal.houseRules) {
    sections.push(journal.houseRules)
  } else {
    const rules: string[] = []
    if (journal.frontMatter.flags.ability_scores_4d6L) {
      rules.push('- Ability scores: 4d6 drop lowest')
    }
    if (journal.frontMatter.flags.level1_max_hp) {
      rules.push('- Level 1: maximum HP')
    }
    if (journal.frontMatter.flags.ascending_ac) {
      rules.push('- Ascending armor class')
    }
    if (rules.length > 0) {
      sections.push(...rules)
    } else {
      sections.push('_No house rules_')
    }
  }
  sections.push('')

  return sections.join('\n')
}

/**
 * Append a session log entry
 */
export function appendSessionLogEntry(journal: ParsedJournal, entry: string): ParsedJournal {
  return {
    ...journal,
    sessionLog: [...journal.sessionLog, entry],
    frontMatter: {
      ...journal.frontMatter,
      updated_at: new Date().toISOString(),
    },
  }
}

/**
 * Update party information
 */
export function updateParty(
  journal: ParsedJournal,
  party: JournalFrontMatter['party']
): ParsedJournal {
  return {
    ...journal,
    frontMatter: {
      ...journal.frontMatter,
      party,
      updated_at: new Date().toISOString(),
    },
  }
}
