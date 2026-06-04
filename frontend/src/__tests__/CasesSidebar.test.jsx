import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import CasesSidebar from '../components/CasesSidebar'

const cases = [
  { case_id: 'case-1', intent: 'motor_claim',  case_status: 'active',   pending_docs: ['RC Book'], total_docs: 3 },
  { case_id: 'case-2', intent: 'health_claim', case_status: 'complete',  pending_docs: [],          total_docs: 5 },
]

describe('CasesSidebar', () => {
  it('renders New Case button', () => {
    render(<CasesSidebar cases={[]} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={vi.fn()} />)
    expect(screen.getByRole('button', { name: /new case/i })).toBeInTheDocument()
  })

  it('calls onNewCase when New Case button is clicked', () => {
    const onNewCase = vi.fn()
    render(<CasesSidebar cases={[]} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={onNewCase} />)
    fireEvent.click(screen.getByRole('button', { name: /new case/i }))
    expect(onNewCase).toHaveBeenCalledTimes(1)
  })

  it('shows empty state when no cases', () => {
    render(<CasesSidebar cases={[]} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={vi.fn()} />)
    expect(screen.getByText(/no cases yet/i)).toBeInTheDocument()
  })

  it('renders each case in the list', () => {
    render(<CasesSidebar cases={cases} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={vi.fn()} />)
    expect(screen.getByText(/motor claim/i)).toBeInTheDocument()
    expect(screen.getByText(/health claim/i)).toBeInTheDocument()
  })

  it('shows Active badge for active cases', () => {
    render(<CasesSidebar cases={cases} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={vi.fn()} />)
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('shows Done badge for complete cases', () => {
    render(<CasesSidebar cases={cases} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={vi.fn()} />)
    expect(screen.getByText('Done')).toBeInTheDocument()
  })

  it('calls onSelectCase with the correct case_id when clicked', () => {
    const onSelectCase = vi.fn()
    render(<CasesSidebar cases={cases} activeCaseId={null} onSelectCase={onSelectCase} onNewCase={vi.fn()} />)
    fireEvent.click(screen.getByText(/motor claim/i))
    expect(onSelectCase).toHaveBeenCalledWith('case-1')
  })

  it('highlights the active case', () => {
    const { container } = render(
      <CasesSidebar cases={cases} activeCaseId="case-1" onSelectCase={vi.fn()} onNewCase={vi.fn()} />
    )
    // Active case should have a distinct background class
    const activeItem = container.querySelector('[class*="bg-brand"]') ||
                       container.querySelector('[class*="bg-indigo"]') ||
                       container.querySelector('[class*="border-brand"]')
    expect(activeItem).toBeInTheDocument()
  })

  it('shows pending doc count for active cases', () => {
    render(<CasesSidebar cases={cases} activeCaseId={null} onSelectCase={vi.fn()} onNewCase={vi.fn()} />)
    expect(screen.getByText(/1 doc/i)).toBeInTheDocument()
  })
})
