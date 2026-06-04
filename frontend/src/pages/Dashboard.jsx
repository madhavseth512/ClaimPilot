import { useEffect, useState, useCallback } from 'react'
import Navbar from '../components/Navbar'
import CasesSidebar from '../components/CasesSidebar'
import ChatArea from '../components/ChatArea'
import DocumentPanel from '../components/DocumentPanel'
import { api } from '../api/client'

export default function Dashboard() {
  const [cases, setCases]               = useState([])
  const [activeCaseId, setActiveCaseId] = useState(null)
  const [chatHistory, setChatHistory]   = useState({})   // { caseId: [msg, ...] }
  const [caseDetails, setCaseDetails]   = useState({})   // { caseId: caseData }
  const [isLoading, setIsLoading]       = useState(false)
  const [uploadingFor, setUploadingFor] = useState(null) // doc name being uploaded

  // Load all cases on mount
  useEffect(() => {
    loadCases()
  }, [])

  async function loadCases() {
    try {
      const data = await api.getCases()
      setCases(data)
      // Load details for each case
      data.forEach(c => refreshCase(c.case_id))
    } catch { /* silently ignore */ }
  }

  async function refreshCase(caseId) {
    try {
      const data = await api.getCase(caseId)
      setCaseDetails(prev => ({ ...prev, [caseId]: data }))
      // Update the cases list entry too
      setCases(prev => prev.map(c => c.case_id === caseId ? { ...c, ...data } : c))
    } catch { /* silently ignore */ }
  }

  async function selectCase(caseId) {
    setActiveCaseId(caseId)
    // If no chat history yet for this case, send a resume signal
    if (!chatHistory[caseId]) {
      setIsLoading(true)
      try {
        const data = await api.resumeSession(caseId)
        if (data?.response) {
          appendMessage(caseId, 'assistant', data.response)
        }
        await refreshCase(caseId)
      } catch { /* silently ignore */ }
      finally { setIsLoading(false) }
    }
  }

  async function startNewCase() {
    setIsLoading(true)
    try {
      // Send "Hello" with no case_id → server creates a new case thread
      const data = await api.sendMessage('Hello', null)
      const newCaseId = data.case_id

      // Add to cases list as a placeholder (intent unknown until classified)
      const placeholder = {
        case_id: newCaseId,
        intent: '',
        case_status: 'active',
        created_at: new Date().toISOString(),
        pending_docs: [],
        collected_docs: [],
        total_docs: 0,
      }
      setCases(prev => [placeholder, ...prev])
      setCaseDetails(prev => ({ ...prev, [newCaseId]: placeholder }))

      // Add onboarding message to chat
      appendMessage(newCaseId, 'assistant', data.response)
      setActiveCaseId(newCaseId)
    } catch (err) {
      console.error('Failed to start new case:', err)
    } finally {
      setIsLoading(false)
    }
  }

  function appendMessage(caseId, role, content) {
    setChatHistory(prev => ({
      ...prev,
      [caseId]: [
        ...(prev[caseId] || []),
        { role, content, timestamp: new Date().toISOString() },
      ],
    }))
  }

  async function handleSend(message) {
    if (!activeCaseId) return
    appendMessage(activeCaseId, 'user', message)
    setIsLoading(true)
    try {
      const data = await api.sendMessage(message, activeCaseId)
      appendMessage(activeCaseId, 'assistant', data.response)
      // Refresh case details (intent / pending docs may have updated)
      await refreshCase(activeCaseId)
    } catch (err) {
      appendMessage(activeCaseId, 'assistant', 'Something went wrong. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  async function handleUpload(file, documentType) {
    if (!activeCaseId) return
    setUploadingFor(documentType)
    try {
      const data = await api.uploadDocument(file, activeCaseId, documentType)
      // Bot acknowledgement from the upload response
      appendMessage(activeCaseId, 'assistant', data.message)
      // Refresh checklist
      await refreshCase(activeCaseId)
    } catch (err) {
      appendMessage(activeCaseId, 'assistant', err.message || 'Upload failed. Please try again.')
    } finally {
      setUploadingFor(null)
    }
  }

  const activeMessages   = chatHistory[activeCaseId]  || []
  const activeCaseData   = caseDetails[activeCaseId]  || null

  return (
    <div className="flex flex-col h-screen overflow-hidden">
      <Navbar />

      <div className="flex flex-1 overflow-hidden">
        {/* Left: cases sidebar */}
        <CasesSidebar
          cases={cases}
          activeCaseId={activeCaseId}
          onSelectCase={selectCase}
          onNewCase={startNewCase}
        />

        {/* Center: chat */}
        {activeCaseId ? (
          <ChatArea
            messages={activeMessages}
            onSend={handleSend}
            isLoading={isLoading}
            caseStatus={activeCaseData?.case_status}
          />
        ) : (
          <div className="flex-1 flex items-center justify-center bg-gray-50">
            <div className="text-center text-gray-400">
              <div className="text-6xl mb-4">🏢</div>
              <h2 className="text-lg font-semibold text-gray-600 mb-2">Welcome to ClaimPilot</h2>
              <p className="text-sm mb-6">Start a new case or select an existing one from the sidebar.</p>
              <button onClick={startNewCase} className="btn-primary">
                Start New Case
              </button>
            </div>
          </div>
        )}

        {/* Right: document panel */}
        <DocumentPanel
          caseData={activeCaseData}
          onUpload={handleUpload}
          uploadingFor={uploadingFor}
        />
      </div>
    </div>
  )
}
