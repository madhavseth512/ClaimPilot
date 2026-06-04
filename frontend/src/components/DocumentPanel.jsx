import { useRef, useState } from 'react'

export default function DocumentPanel({ caseData, onUpload, uploadingFor }) {
  const fileInputRef = useRef()
  const [activeUpload, setActiveUpload] = useState(null)
  const [previewDoc, setPreviewDoc] = useState(null) // { name, url }

  if (!caseData) {
    return (
      <aside className="w-72 bg-white border-l border-gray-200 flex items-center justify-center">
        <p className="text-xs text-gray-400 text-center px-4">
          Select or start a case to see document checklist.
        </p>
      </aside>
    )
  }

  const { intent, pending_docs = [], collected_docs = [], total_docs, case_status } = caseData
  const allDocs = [
    ...collected_docs.map(d => ({ name: d, collected: true })),
    ...pending_docs.map(d => ({ name: d, collected: false })),
  ]
  const progress = total_docs > 0 ? Math.round((collected_docs.length / total_docs) * 100) : 0

  function triggerUpload(docName) {
    setActiveUpload(docName)
    fileInputRef.current.click()
  }

  async function handleFileChange(e) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file || !activeUpload) return
    await onUpload(file, activeUpload)
    setActiveUpload(null)
  }

  function handlePreview(docName) {
    // For uploaded docs, we can't retrieve the file blob from server yet
    // Show a simple info modal instead
    setPreviewDoc({ name: docName })
  }

  return (
    <aside className="w-72 bg-white border-l border-gray-200 flex flex-col flex-shrink-0">
      {/* Header */}
      <div className="px-4 py-4 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-800">Document Checklist</h2>
        {intent && (
          <p className="text-xs text-gray-500 mt-0.5 capitalize">
            {intent.replace(/_/g, ' ')}
          </p>
        )}

        {/* Progress bar */}
        {total_docs > 0 && (
          <div className="mt-3">
            <div className="flex justify-between text-xs text-gray-500 mb-1">
              <span>{collected_docs.length} of {total_docs} collected</span>
              <span>{progress}%</span>
            </div>
            <div className="h-1.5 bg-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  progress === 100 ? 'bg-green-500' : 'bg-brand-600'}`}
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Document list */}
      <div className="flex-1 overflow-y-auto py-2">
        {allDocs.length === 0 ? (
          <p className="text-xs text-gray-400 text-center py-6 px-4">
            Document checklist will appear once your intent is identified.
          </p>
        ) : (
          allDocs.map((doc, i) => (
            <div key={i} className="flex items-center gap-3 px-4 py-2.5 border-b border-gray-50 last:border-0">
              {/* Status icon */}
              <div className={`w-5 h-5 rounded-full flex items-center justify-center flex-shrink-0
                ${doc.collected ? 'bg-green-100' : 'bg-gray-100'}`}>
                {doc.collected ? (
                  <svg className="w-3 h-3 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <div className="w-2 h-2 rounded-full bg-gray-400" />
                )}
              </div>

              {/* Doc name */}
              <span className={`text-xs flex-1 leading-tight
                ${doc.collected ? 'text-gray-500 line-through' : 'text-gray-800 font-medium'}`}>
                {doc.name}
              </span>

              {/* Action button */}
              {doc.collected ? (
                <button
                  onClick={() => handlePreview(doc.name)}
                  className="text-[10px] text-brand-600 hover:underline flex-shrink-0"
                >
                  View
                </button>
              ) : case_status !== 'complete' && (
                <button
                  onClick={() => triggerUpload(doc.name)}
                  disabled={uploadingFor === doc.name}
                  className="text-[10px] bg-brand-600 text-white px-2 py-0.5 rounded flex-shrink-0
                             hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploadingFor === doc.name ? '…' : 'Upload'}
                </button>
              )}
            </div>
          ))
        )}
      </div>

      {/* Completion banner */}
      {case_status === 'complete' && (
        <div className="bg-green-50 border-t border-green-200 px-4 py-3 flex items-center gap-2">
          <span className="text-green-600">✅</span>
          <p className="text-xs text-green-800 font-medium">Case submitted successfully</p>
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Preview modal */}
      {previewDoc && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50"
          onClick={() => setPreviewDoc(null)}>
          <div className="card w-80 p-6" onClick={e => e.stopPropagation()}>
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-brand-100 rounded-lg flex items-center justify-center text-lg">📄</div>
              <div>
                <p className="text-sm font-semibold text-gray-800">{previewDoc.name}</p>
                <p className="text-xs text-green-600">Collected ✓</p>
              </div>
            </div>
            <p className="text-xs text-gray-500">
              This document has been received and is stored securely in your claim file.
            </p>
            <button className="btn-primary w-full mt-4 text-sm" onClick={() => setPreviewDoc(null)}>
              Close
            </button>
          </div>
        </div>
      )}
    </aside>
  )
}
