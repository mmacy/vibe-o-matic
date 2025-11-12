import { useState, useRef, useEffect } from 'react'
import { useAppStore } from '../state/store'
import DiceAudit from './DiceAudit'
import { nanoid } from 'nanoid'
import { createClient } from '@/lib/openai/client'
import { getGMResponse } from '@/lib/openai/orchestration'
import { updateParty } from '@/lib/journal/serialize'
import { normalizeCharacterForJournal } from '@/app/state/schema'
import type { ChatCompletionMessageParam } from 'openai/resources/chat/completions'
import ReactMarkdown from 'react-markdown'

export default function ChatPanel() {
  const {
    apiKey,
    messages,
    addMessage,
    isLoading,
    setLoading,
    setError,
    rulesPdf,
    modulePdf,
    journal,
    updateJournal,
    addToJournalCache,
    settings,
  } = useAppStore()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !apiKey || !rulesPdf || !modulePdf) return

    const userMessage = {
      id: nanoid(),
      role: 'user' as const,
      content: input.trim(),
      timestamp: new Date().toISOString(),
    }

    addMessage(userMessage)
    setInput('')
    setLoading(true)
    setError(null)

    // Focus input after sending
    setTimeout(() => {
      inputRef.current?.focus()
    }, 0)

    try {
      const client = createClient(apiKey)

      // Build messages for API
      const apiMessages: ChatCompletionMessageParam[] = messages.map((msg) => ({
        role: msg.role,
        content: msg.content,
      }))
      apiMessages.push({
        role: 'user',
        content: userMessage.content,
      })

      // Get GM response
      const response = await getGMResponse({
        client,
        messages: apiMessages,
        rulesContext: rulesPdf.fullText,
        moduleContext: modulePdf.fullText,
        journal,
        model: settings.model,
        settings,
      })

      const assistantMessage = {
        id: nanoid(),
        role: 'assistant' as const,
        content: response.text,
        timestamp: new Date().toISOString(),
        dice_audit: response.diceAudit,
      }

      addMessage(assistantMessage)

      // Add interaction to journal cache for later AI summarization
      addToJournalCache({
        userMessage: userMessage.content,
        gmResponse: response.text,
        timestamp: assistantMessage.timestamp,
        diceAudit: response.diceAudit,
        createdCharacters: response.createdCharacters,
      })

      // Update party with newly created characters immediately
      if (journal && response.createdCharacters && response.createdCharacters.length > 0) {
        updateJournal((j) => {
          const currentParty = j.frontMatter.party
          const newParty = [...currentParty]

          // Merge characters: update existing or add new
          // Normalize characters to convert nullable fields to defaults for journal persistence
          for (const character of response.createdCharacters) {
            const normalized = normalizeCharacterForJournal(character)
            const existingIndex = newParty.findIndex(
              (c) => c.name.toLowerCase() === normalized.name.toLowerCase()
            )

            if (existingIndex >= 0) {
              // Update existing character
              newParty[existingIndex] = normalized
            } else {
              // Add new character
              newParty.push(normalized)
            }
          }

          return updateParty(j, newParty)
        })
      }
    } catch (error) {
      console.error('Error getting GM response:', error)
      setError(error instanceof Error ? error.message : 'Unknown error occurred')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="flex h-full items-center justify-center text-text-muted">
            <p>Start your adventure by sending a message...</p>
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'ml-auto max-w-2xl bg-primary text-white'
                    : 'mr-auto max-w-3xl bg-background-lighter'
                }`}
              >
                <div className="prose prose-invert max-w-none">
                  <ReactMarkdown>{message.content}</ReactMarkdown>
                </div>
                {message.dice_audit && message.dice_audit.length > 0 && (
                  <DiceAudit rolls={message.dice_audit} />
                )}
              </div>
            ))}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t border-slate-700 bg-background-lighter p-4">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your action..."
            disabled={isLoading || !apiKey || !rulesPdf || !modulePdf}
            className="input flex-1"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim() || !apiKey || !rulesPdf || !modulePdf}
            className="btn-primary"
          >
            {isLoading ? 'Thinking...' : 'Send'}
          </button>
        </form>
      </div>
    </div>
  )
}
