import { useState } from 'react'
import { useAppStore } from '../state/store'
import { serializeJournal, appendSessionLogEntry } from '@/lib/journal/serialize'
import { formatTimestamp } from '@/lib/ui/formatting'
import { summarizeJournalCache } from '@/lib/journal/summarize'
import { createClient } from '@/lib/openai/client'

export default function JournalDrawer() {
  const {
    isJournalOpen,
    setJournalOpen,
    journal,
    journalEntryCache,
    clearJournalCache,
    updateJournal,
    apiKey,
    settings,
  } = useAppStore()

  const [isSummarizing, setIsSummarizing] = useState(false)
  const [summarizeError, setSummarizeError] = useState<string | null>(null)

  if (!isJournalOpen) return null

  const handleDownload = () => {
    if (!journal) return

    const markdown = serializeJournal(journal)
    const blob = new Blob([markdown], { type: 'text/markdown' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `ai-gm-journal-${Date.now()}.md`
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleSummarize = async () => {
    if (!apiKey || !journal || journalEntryCache.length === 0) return

    setIsSummarizing(true)
    setSummarizeError(null)

    try {
      const client = createClient(apiKey)
      const summary = await summarizeJournalCache(client, journalEntryCache, settings.model)

      // Add summary to journal
      updateJournal((j) => appendSessionLogEntry(j, summary))

      // Clear the cache
      clearJournalCache()
    } catch (error) {
      console.error('Error summarizing journal cache:', error)
      setSummarizeError(error instanceof Error ? error.message : 'Failed to summarize')
    } finally {
      setIsSummarizing(false)
    }
  }

  return (
    <>
      <div className="drawer-overlay" onClick={() => setJournalOpen(false)} />
      <div className="drawer z-50 w-96 overflow-y-auto p-6">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold">Journal</h2>
          <button onClick={() => setJournalOpen(false)} className="text-2xl hover:text-primary">
            ×
          </button>
        </div>

        {journal ? (
          <div className="space-y-6">
            <section>
              <div className="mb-2 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Info</h3>
                <button onClick={handleDownload} className="btn-primary text-sm">
                  Download
                </button>
              </div>
              <div className="space-y-1 text-sm text-text-muted">
                <p>System: {journal.frontMatter.system}</p>
                <p>Created: {formatTimestamp(journal.frontMatter.created_at)}</p>
                <p>Updated: {formatTimestamp(journal.frontMatter.updated_at)}</p>
              </div>
            </section>

            <section>
              <h3 className="mb-3 text-lg font-semibold">Party</h3>
              {journal.frontMatter.party.length > 0 ? (
                <div className="space-y-4">
                  {journal.frontMatter.party.map((char, index) => (
                    <div key={index} className="rounded bg-background p-3">
                      <h4 className="mb-1 font-bold">{char.name}</h4>
                      <p className="text-sm text-text-muted">
                        {char.class}, Level {char.level}
                      </p>
                      <p className="text-sm">
                        HP: {char.hp}/{char.max_hp} | AC: {char.ac}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-text-muted">No characters yet</p>
              )}
            </section>

            <section>
              <div className="mb-3 flex items-center justify-between">
                <h3 className="text-lg font-semibold">Pending Entries</h3>
                <button
                  onClick={handleSummarize}
                  disabled={journalEntryCache.length === 0 || !apiKey || isSummarizing}
                  className="btn-primary text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isSummarizing ? 'Summarizing...' : 'Summarize to Journal'}
                </button>
              </div>
              {journalEntryCache.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-sm text-text-muted">
                    {journalEntryCache.length} interaction{journalEntryCache.length !== 1 ? 's' : ''} waiting to be summarized
                  </p>
                  {summarizeError && (
                    <p className="text-sm text-red-400">{summarizeError}</p>
                  )}
                </div>
              ) : (
                <p className="text-sm text-text-muted">No pending interactions</p>
              )}
            </section>

            <section>
              <h3 className="mb-3 text-lg font-semibold">Session log</h3>
              {journal.sessionLog.length > 0 ? (
                <div className="space-y-1 text-sm">
                  {journal.sessionLog.map((entry, index) => (
                    <p key={index} className="text-text-muted">
                      {entry}
                    </p>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-text-muted">No entries yet</p>
              )}
            </section>
          </div>
        ) : (
          <p className="text-text-muted">No journal loaded</p>
        )}
      </div>
    </>
  )
}
