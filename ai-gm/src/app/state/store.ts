import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { ChatMessage, Settings, JournalEntryCache } from './schema'
import type { ParsedDocument } from '@/lib/pdf/extract'
import type { ParsedJournal } from '@/lib/journal/parse'
import { createDefaultJournal } from '@/lib/journal/parse'

interface AppState {
  // API Key (volatile, cleared on unload)
  apiKey: string | null
  setApiKey: (key: string | null) => void

  // Settings
  settings: Settings
  updateSettings: (settings: Partial<Settings>) => void
  addToFileHistory: (type: 'rules_pdf' | 'module_pdf' | 'journal_file', path: string) => void

  // Uploaded documents
  rulesPdf: ParsedDocument | null
  modulePdf: ParsedDocument | null
  setRulesPdf: (doc: ParsedDocument | null) => void
  setModulePdf: (doc: ParsedDocument | null) => void

  // Journal
  journal: ParsedJournal | null
  setJournal: (journal: ParsedJournal | null) => void
  updateJournal: (updater: (journal: ParsedJournal) => ParsedJournal) => void

  // Journal entry cache (in-memory before AI summarization)
  journalEntryCache: JournalEntryCache[]
  addToJournalCache: (entry: JournalEntryCache) => void
  clearJournalCache: () => void

  // Chat messages
  messages: ChatMessage[]
  addMessage: (message: ChatMessage) => void
  clearMessages: () => void

  // UI state
  isSettingsOpen: boolean
  isJournalOpen: boolean
  setSettingsOpen: (open: boolean) => void
  setJournalOpen: (open: boolean) => void

  // Session state
  isSessionActive: boolean
  isLoading: boolean
  error: string | null
  setSessionActive: (active: boolean) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void

  // Initialize journal
  initializeJournal: () => void
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      // API Key
      apiKey: null,
      setApiKey: (key) => set({ apiKey: key }),

      // Settings
      settings: {
        ability_scores_4d6L: false,
        level1_max_hp: false,
        model: 'gpt-4o-2024-08-06',
        temperature: 1,
        max_tokens: undefined,
        rules_pdf_path: undefined,
        module_pdf_path: undefined,
        rules_pdf_history: [],
        module_pdf_history: [],
        journal_file_history: [],
      },
      updateSettings: (newSettings) =>
        set((state) => ({
          settings: { ...state.settings, ...newSettings },
        })),
      addToFileHistory: (type, path) =>
        set((state) => {
          const historyKey = `${type}_history` as keyof Settings
          const pathKey = `${type}_path` as keyof Settings
          const currentHistory = (state.settings[historyKey] as string[]) || []

          // Remove the path if it already exists to avoid duplicates
          const filteredHistory = currentHistory.filter((p) => p !== path)

          // Add the new path to the beginning and keep only last 4
          const newHistory = [path, ...filteredHistory].slice(0, 4)

          return {
            settings: {
              ...state.settings,
              [historyKey]: newHistory,
              [pathKey]: path,
            },
          }
        }),

  // Documents
  rulesPdf: null,
  modulePdf: null,
  setRulesPdf: (doc) => set({ rulesPdf: doc }),
  setModulePdf: (doc) => set({ modulePdf: doc }),

  // Journal
  journal: null,
  setJournal: (journal) => set({ journal }),
  updateJournal: (updater) =>
    set((state) => ({
      journal: state.journal ? updater(state.journal) : null,
    })),

  // Journal entry cache
  journalEntryCache: [],
  addToJournalCache: (entry) =>
    set((state) => ({
      journalEntryCache: [...state.journalEntryCache, entry],
    })),
  clearJournalCache: () => set({ journalEntryCache: [] }),

  // Messages
  messages: [],
  addMessage: (message) =>
    set((state) => ({
      messages: [...state.messages, message],
    })),
  clearMessages: () => set({ messages: [] }),

  // UI state
  isSettingsOpen: false,
  isJournalOpen: false,
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),
  setJournalOpen: (open) => set({ isJournalOpen: open }),

  // Session state
  isSessionActive: false,
  isLoading: false,
  error: null,
  setSessionActive: (active) => set({ isSessionActive: active }),
  setLoading: (loading) => set({ isLoading: loading }),
  setError: (error) => set({ error }),

      // Initialize journal
      initializeJournal: () => {
        const state = get()
        if (!state.journal) {
          const defaultJournal = createDefaultJournal('BX', state.settings)
          set({ journal: defaultJournal })
        }
      },
    }),
    {
      name: 'vibe-o-matic-storage',
      partialize: (state) => ({ settings: state.settings }),
      storage: createJSONStorage(() => {
        // SSR-safe storage: only use localStorage in browser environment
        if (typeof window !== 'undefined') {
          return localStorage
        }
        // Return a no-op storage for SSR
        return {
          getItem: () => null,
          setItem: () => {},
          removeItem: () => {},
        }
      }),
      merge: (persistedState, currentState) => {
        // Merge persisted state with current state, ensuring new fields have defaults
        const persisted = persistedState as Partial<AppState>
        return {
          ...currentState,
          ...persisted,
          settings: {
            ...currentState.settings,
            ...(persisted.settings || {}),
            // Ensure history arrays always exist
            rules_pdf_history: persisted.settings?.rules_pdf_history || [],
            module_pdf_history: persisted.settings?.module_pdf_history || [],
            journal_file_history: persisted.settings?.journal_file_history || [],
          },
        }
      },
    }
  )
)

// Clear API key on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    useAppStore.getState().setApiKey(null)
  })
}
