import { create } from 'zustand'
import type { ChatMessage, Settings } from './schema'
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

  // Uploaded documents
  rulesPdf: ParsedDocument | null
  modulePdf: ParsedDocument | null
  setRulesPdf: (doc: ParsedDocument | null) => void
  setModulePdf: (doc: ParsedDocument | null) => void

  // Journal
  journal: ParsedJournal | null
  setJournal: (journal: ParsedJournal | null) => void
  updateJournal: (updater: (journal: ParsedJournal) => ParsedJournal) => void

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

export const useAppStore = create<AppState>((set, get) => ({
  // API Key
  apiKey: null,
  setApiKey: (key) => set({ apiKey: key }),

  // Settings
  settings: {
    ability_scores_4d6L: false,
    level1_max_hp: false,
    model: 'gpt-4o-2024-08-06',
  },
  updateSettings: (newSettings) =>
    set((state) => ({
      settings: { ...state.settings, ...newSettings },
    })),

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
}))

// Clear API key on page unload
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    useAppStore.getState().setApiKey(null)
  })
}
