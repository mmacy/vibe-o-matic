import { useAppStore } from '../state/store'

export default function TopBar() {
  const { setSettingsOpen, setJournalOpen, apiKey } = useAppStore()

  return (
    <div className="flex items-center justify-between border-b border-slate-700 bg-background-lighter px-6 py-4">
      <h1 className="text-2xl font-bold">AI Game Master</h1>
      <div className="flex items-center gap-4">
        {apiKey && (
          <span className="text-sm text-green-400" title="API key is set">
            ● Key set
          </span>
        )}
        <button onClick={() => setJournalOpen(true)} className="btn-secondary">
          Journal
        </button>
        <button onClick={() => setSettingsOpen(true)} className="btn-secondary">
          Settings
        </button>
      </div>
    </div>
  )
}
