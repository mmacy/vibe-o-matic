import { useRef } from 'react'

interface PdfUploadProps {
  label: string
  onUpload: (file: File) => Promise<void>
  isUploaded: boolean
}

export default function PdfUpload({ label, onUpload, isUploaded }: PdfUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file && file.type === 'application/pdf') {
      await onUpload(file)
    }
  }

  return (
    <div className="flex items-center gap-3">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
        className="hidden"
        id={`upload-${label.toLowerCase().replace(/\s+/g, '-')}`}
      />
      <label
        htmlFor={`upload-${label.toLowerCase().replace(/\s+/g, '-')}`}
        className="btn-secondary cursor-pointer"
      >
        {isUploaded ? '✓ ' : ''}
        {label}
      </label>
    </div>
  )
}
