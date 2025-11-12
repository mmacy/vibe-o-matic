import { useAppStore } from '../state/store'
import { formatLabel } from '@/lib/ui/formatting'

export default function SettingsDrawer() {
  const { isSettingsOpen, setSettingsOpen, settings, updateSettings } = useAppStore()

  // GPT-5 models don't support temperature or max_tokens parameters
  const isGPT5Model = settings.model.toLowerCase().includes('gpt-5')

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
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={settings.ascending_ac}
                  onChange={(e) => updateSettings({ ascending_ac: e.target.checked })}
                  className="h-4 w-4 rounded border-slate-700 bg-background text-primary focus:ring-2 focus:ring-primary"
                />
                <span>{formatLabel('ascending_ac')}</span>
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
              <option value="gpt-5">GPT-5</option>
              <option value="gpt-5-mini">GPT-5 Mini</option>
              <option value="gpt-5-nano">GPT-5 Nano</option>
              <option value="gpt-4.1">GPT-4.1</option>
              <option value="gpt-4o-2024-08-06">GPT-4o (2024-08-06)</option>
              <option value="gpt-4o-mini">GPT-4o Mini</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </select>
          </section>

          <section>
            <h3 className="mb-3 text-lg font-semibold">LLM Configuration</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-text-muted">
                  Temperature (0-2)
                </label>
                <input
                  type="number"
                  min="0"
                  max="2"
                  step="0.1"
                  value={settings.temperature}
                  onChange={(e) => {
                    const value = parseFloat(e.target.value)
                    updateSettings({ temperature: isNaN(value) ? 1 : value })
                  }}
                  disabled={isGPT5Model}
                  className="input w-full disabled:cursor-not-allowed disabled:opacity-50"
                />
                <p className="mt-1 text-xs text-text-muted">
                  {isGPT5Model
                    ? 'Not supported by GPT-5 models'
                    : 'Higher values make output more random, lower values more focused'}
                </p>
              </div>
              <div>
                <label className="mb-1 block text-sm text-text-muted">
                  Max Output Tokens (optional)
                </label>
                <input
                  type="number"
                  min="1"
                  max="16000"
                  step="100"
                  value={settings.max_tokens ?? ''}
                  onChange={(e) =>
                    updateSettings({
                      max_tokens: e.target.value ? parseInt(e.target.value) : undefined
                    })
                  }
                  placeholder="Default (model-specific)"
                  disabled={isGPT5Model}
                  className="input w-full disabled:cursor-not-allowed disabled:opacity-50"
                />
                <p className="mt-1 text-xs text-text-muted">
                  {isGPT5Model
                    ? 'Not supported by GPT-5 models (uses max_completion_tokens instead)'
                    : 'Limits the length of GM responses'}
                </p>
              </div>
            </div>
          </section>

          <section>
            <h3 className="mb-3 text-lg font-semibold">Document Paths</h3>
            <div className="space-y-3">
              <div>
                <label className="mb-1 block text-sm text-text-muted">
                  Rules PDF Path (optional)
                </label>
                <input
                  type="text"
                  value={settings.rules_pdf_path ?? ''}
                  onChange={(e) => updateSettings({ rules_pdf_path: e.target.value || undefined })}
                  placeholder="/path/to/rules.pdf"
                  className="input w-full font-mono text-sm"
                />
                <p className="mt-1 text-xs text-text-muted">
                  Auto-load rules from this path when starting a session
                </p>
              </div>
              <div>
                <label className="mb-1 block text-sm text-text-muted">
                  Module PDF Path (optional)
                </label>
                <input
                  type="text"
                  value={settings.module_pdf_path ?? ''}
                  onChange={(e) => updateSettings({ module_pdf_path: e.target.value || undefined })}
                  placeholder="/path/to/module.pdf"
                  className="input w-full font-mono text-sm"
                />
                <p className="mt-1 text-xs text-text-muted">
                  Auto-load module from this path when starting a session
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </>
  )
}
