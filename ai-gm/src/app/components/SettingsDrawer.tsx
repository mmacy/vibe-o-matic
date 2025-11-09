import { useAppStore } from '../state/store'
import { formatLabel } from '@/lib/ui/formatting'

export default function SettingsDrawer() {
  const { isSettingsOpen, setSettingsOpen, settings, updateSettings } = useAppStore()

  if (!isSettingsOpen) return null

  return (
    <>
      <div className="drawer-overlay" onClick={() => setSettingsOpen(false)} />
      <div className="drawer z-50 w-96 p-6">
        <div className="mb-6 flex items-center justify-between">
          <h2 className="text-2xl font-bold">Settings</h2>
          <button onClick={() => setSettingsOpen(false)} className="text-2xl hover:text-primary">
            ×
          </button>
        </div>

        <div className="space-y-6">
          <section>
            <h3 className="mb-3 text-lg font-semibold">Homebrew rules</h3>
            <div className="space-y-3">
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={settings.ability_scores_4d6L}
                  onChange={(e) => updateSettings({ ability_scores_4d6L: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-background text-primary focus:ring-2 focus:ring-primary"
                />
                <span>{formatLabel('ability_scores_4d6L')}</span>
              </label>
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={settings.level1_max_hp}
                  onChange={(e) => updateSettings({ level1_max_hp: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-background text-primary focus:ring-2 focus:ring-primary"
                />
                <span>{formatLabel('level1_max_hp')}</span>
              </label>
            </div>
          </section>

          <section>
            <h3 className="mb-3 text-lg font-semibold">Model</h3>
            <select
              value={settings.model}
              onChange={(e) => updateSettings({ model: e.target.value })}
              className="input w-full"
            >
              <option value="gpt-4o-2024-08-06">GPT-4o (2024-08-06)</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </select>
          </section>
        </div>
      </div>
    </>
  )
}
