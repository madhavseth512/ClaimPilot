import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import DocumentPanel from '../components/DocumentPanel'

const activeCaseData = {
  intent: 'motor_claim',
  pending_docs: ['RC Book', 'Driving Licence'],
  collected_docs: ['FIR Copy'],
  total_docs: 3,
  case_status: 'active',
}

describe('DocumentPanel', () => {
  it('shows placeholder when no case is selected', () => {
    render(<DocumentPanel caseData={null} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText(/select or start a case/i)).toBeInTheDocument()
  })

  it('renders intent label', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText(/motor claim/i)).toBeInTheDocument()
  })

  it('shows collected documents with checkmark', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText('FIR Copy')).toBeInTheDocument()
  })

  it('shows pending documents with Upload button', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText('RC Book')).toBeInTheDocument()
    expect(screen.getByText('Driving Licence')).toBeInTheDocument()
    const uploadBtns = screen.getAllByRole('button', { name: /upload/i })
    expect(uploadBtns).toHaveLength(2)
  })

  it('shows correct progress percentage', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText('1 of 3 collected')).toBeInTheDocument()
    expect(screen.getByText('33%')).toBeInTheDocument()
  })

  it('shows 100% progress when all docs collected', () => {
    const completedCase = {
      ...activeCaseData,
      pending_docs: [],
      collected_docs: ['FIR Copy', 'RC Book', 'Driving Licence'],
      case_status: 'complete',
    }
    render(<DocumentPanel caseData={completedCase} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText('3 of 3 collected')).toBeInTheDocument()
    expect(screen.getByText('100%')).toBeInTheDocument()
  })

  it('hides upload buttons when case is complete', () => {
    const completedCase = {
      ...activeCaseData,
      pending_docs: ['RC Book'],
      case_status: 'complete',
    }
    render(<DocumentPanel caseData={completedCase} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.queryByRole('button', { name: /upload/i })).not.toBeInTheDocument()
  })

  it('shows case complete banner when status is complete', () => {
    const completedCase = { ...activeCaseData, pending_docs: [], case_status: 'complete' }
    render(<DocumentPanel caseData={completedCase} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByText(/submitted successfully/i)).toBeInTheDocument()
  })

  it('shows loading state on Upload button while uploading', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor="RC Book" />)
    // The uploading button shows "…" instead of "Upload"
    expect(screen.getByText('…')).toBeInTheDocument()
  })

  it('shows View button for collected docs', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    expect(screen.getByRole('button', { name: /view/i })).toBeInTheDocument()
  })

  it('shows preview modal when View is clicked', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    fireEvent.click(screen.getByRole('button', { name: /view/i }))
    expect(screen.getByText(/received and is stored securely/i)).toBeInTheDocument()
  })

  it('closes preview modal when Close is clicked', () => {
    render(<DocumentPanel caseData={activeCaseData} onUpload={vi.fn()} uploadingFor={null} />)
    fireEvent.click(screen.getByRole('button', { name: /view/i }))
    fireEvent.click(screen.getByRole('button', { name: /close/i }))
    expect(screen.queryByText(/received and is stored securely/i)).not.toBeInTheDocument()
  })
})
