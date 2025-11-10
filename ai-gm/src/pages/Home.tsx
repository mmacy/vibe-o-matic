import { useState } from 'react'
import { useAppStore } from '../app/state/store'
import KeyInputModal from '../app/components/KeyInputModal'
import PdfUpload from '../app/components/PdfUpload'
import ChatPanel from '../app/components/ChatPanel'
import { extractTextFromPDF } from '@/lib/pdf/extract'
import { parseJournal } from '@/lib/journal/parse'

export default function Home() {
  const {
    apiKey,
    setApiKey,
    rulesPdf,
    modulePdf,
    journal,
    setRulesPdf,
    setModulePdf,
    setJournal,
    isSessionActive,
    setSessionActive,
    initializeJournal,
    error,
    setError,
    settings,
    addToFileHistory,
  } = useAppStore()

  const [isKeyModalOpen, setIsKeyModalOpen] = useState(false)
  const [isUploading, setIsUploading] = useState(false)

  const handleApiKeySubmit = (key: string) => {
    setApiKey(key)
    setIsKeyModalOpen(false)
  }

  const handleRulesUpload = async (file: File) => {
    setIsUploading(true)
    setError(null)
    try {
      const doc = await extractTextFromPDF(file)
      setRulesPdf(doc)
      // Add file name to history
      addToFileHistory('rules_pdf', file.name)
    } catch (error) {
      setError('Failed to parse rules PDF')
      console.error(error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleModuleUpload = async (file: File) => {
    setIsUploading(true)
    setError(null)
    try {
      const doc = await extractTextFromPDF(file)
      setModulePdf(doc)
      // Add file name to history
      addToFileHistory('module_pdf', file.name)
    } catch (error) {
      setError('Failed to parse module PDF')
      console.error(error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleJournalUpload = async (file: File) => {
    setIsUploading(true)
    setError(null)
    try {
      const text = await file.text()
      const parsed = parseJournal(text)
      setJournal(parsed)
      // Add file name to history
      addToFileHistory('journal_file', file.name)
    } catch (error) {
      setError('Failed to parse journal file')
      console.error(error)
    } finally {
      setIsUploading(false)
    }
  }

  const handleStartSession = () => {
    if (!journal) {
      initializeJournal()
    }
    setSessionActive(true)
  }

  if (isSessionActive) {
    return <ChatPanel />
  }

  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="w-full max-w-2xl space-y-6">
        <div className="text-center">
          <h2 className="mb-2 text-3xl font-bold">Welcome to AI Game Master</h2>
          <p className="text-text-muted">
            Run a rules-faithful B/X-compatible session with an AI GM
          </p>
        </div>

        {error && (
          <div className="rounded-lg bg-red-900/20 p-4 text-red-400">
            <p className="font-semibold">Error</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        <div className="space-y-4 rounded-lg bg-background-lighter p-6">
          <h3 className="text-xl font-semibold">Setup</h3>

          {/* API Key */}
          <div>
            <label className="mb-2 block text-sm font-medium">OpenAI API key</label>
            {apiKey ? (
              <div className="flex items-center gap-2">
                <span className="text-sm text-green-400">✓ Key set</span>
                <button
                  onClick={() => setIsKeyModalOpen(true)}
                  className="text-sm text-primary hover:underline"
                >
                  Change
                </button>
              </div>
            ) : (
              <button onClick={() => setIsKeyModalOpen(true)} className="btn-primary">
                Enter API key
              </button>
            )}
          </div>

          {/* PDFs */}
          <div>
            <label className="mb-2 block text-sm font-medium">Upload materials</label>
            <div className="space-y-4">
              <div>
                <PdfUpload
                  label="Rules PDF"
                  onUpload={handleRulesUpload}
                  isUploaded={!!rulesPdf}
                />
                {settings.rules_pdf_history?.length > 0 && (
                  <div className="mt-2 text-xs text-text-muted">
                    <div className="mb-1">Recent files:</div>
                    <ul className="ml-4 list-disc space-y-1">
                      {settings.rules_pdf_history?.map((path, idx) => (
                        <li key={idx} className={idx === 0 ? 'font-semibold' : ''}>
                          {path}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
              <div>
                <PdfUpload
                  label="Module PDF"
                  onUpload={handleModuleUpload}
                  isUploaded={!!modulePdf}
                />
                {settings.module_pdf_history?.length > 0 && (
                  <div className="mt-2 text-xs text-text-muted">
                    <div className="mb-1">Recent files:</div>
                    <ul className="ml-4 list-disc space-y-1">
                      {settings.module_pdf_history?.map((path, idx) => (
                        <li key={idx} className={idx === 0 ? 'font-semibold' : ''}>
                          {path}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Optional Journal */}
          <div>
            <label className="mb-2 block text-sm font-medium">Journal (optional)</label>
            <div className="space-y-2">
              {journal ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-green-400">✓ Journal loaded</span>
                  <button
                    onClick={() => setJournal(null)}
                    className="text-sm text-primary hover:underline"
                  >
                    Clear
                  </button>
                </div>
              ) : (
                <>
                  <input
                    type="file"
                    accept=".md,.txt"
                    onChange={(e) => {
                      const file = e.target.files?.[0]
                      if (file) handleJournalUpload(file)
                    }}
                    className="hidden"
                    id="upload-journal"
                  />
                  <label htmlFor="upload-journal" className="btn-secondary cursor-pointer">
                    Upload existing journal
                  </label>
                  <p className="text-xs text-text-muted">
                    Or skip to start fresh with character creation
                  </p>
                </>
              )}
              {settings.journal_file_history?.length > 0 && (
                <div className="mt-2 text-xs text-text-muted">
                  <div className="mb-1">Recent files:</div>
                  <ul className="ml-4 list-disc space-y-1">
                    {settings.journal_file_history?.map((path, idx) => (
                      <li key={idx} className={idx === 0 ? 'font-semibold' : ''}>
                        {path}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        <button
          onClick={handleStartSession}
          disabled={!apiKey || !rulesPdf || !modulePdf || isUploading}
          className="btn-primary w-full"
        >
          {isUploading ? 'Processing...' : 'Start session'}
        </button>
      </div>

      <KeyInputModal
        isOpen={isKeyModalOpen}
        onSubmit={handleApiKeySubmit}
        onClose={() => setIsKeyModalOpen(false)}
      />
    </div>
  )
}
