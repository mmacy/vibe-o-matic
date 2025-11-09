import { useState } from 'react'

interface KeyInputModalProps {
  isOpen: boolean
  onSubmit: (key: string) => void
  onClose: () => void
}

export default function KeyInputModal({ isOpen, onSubmit, onClose }: KeyInputModalProps) {
  const [apiKey, setApiKey] = useState('')

  if (!isOpen) return null

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (apiKey.trim()) {
      onSubmit(apiKey.trim())
      setApiKey('')
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="drawer-overlay" onClick={onClose} />
      <div className="relative z-10 w-full max-w-md rounded-lg bg-background-lighter p-6 shadow-2xl">
        <h2 className="mb-4 text-2xl font-bold">Enter OpenAI API key</h2>
        <p className="mb-4 text-sm text-text-muted">
          Your API key is stored only in memory and will be cleared when you close this tab. It is
          never persisted or sent anywhere except to OpenAI.
        </p>
        <form onSubmit={handleSubmit}>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk-..."
            className="input mb-4 w-full"
            autoFocus
          />
          <div className="flex gap-2">
            <button type="submit" className="btn-primary flex-1">
              Submit
            </button>
            <button type="button" onClick={onClose} className="btn-secondary">
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
