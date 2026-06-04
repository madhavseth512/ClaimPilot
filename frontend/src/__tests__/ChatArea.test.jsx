import { render, screen, fireEvent } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import ChatArea from '../components/ChatArea'

const messages = [
  { role: 'assistant', content: 'Hello! I am ClaimPilot.', timestamp: new Date().toISOString() },
  { role: 'user',      content: 'I had a car accident.',   timestamp: new Date().toISOString() },
]

describe('ChatArea', () => {
  it('renders all messages', () => {
    render(<ChatArea messages={messages} onSend={vi.fn()} isLoading={false} caseStatus="active" />)
    expect(screen.getByText('Hello! I am ClaimPilot.')).toBeInTheDocument()
    expect(screen.getByText('I had a car accident.')).toBeInTheDocument()
  })

  it('shows empty state when no messages', () => {
    render(<ChatArea messages={[]} onSend={vi.fn()} isLoading={false} caseStatus="active" />)
    expect(screen.getByText(/start the conversation/i)).toBeInTheDocument()
  })

  it('calls onSend when Send button is clicked', () => {
    const onSend = vi.fn()
    render(<ChatArea messages={[]} onSend={onSend} isLoading={false} caseStatus="active" />)
    const textarea = screen.getByPlaceholderText(/type a message/i)
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(onSend).toHaveBeenCalledWith('Hello')
  })

  it('calls onSend when Enter key is pressed', () => {
    const onSend = vi.fn()
    render(<ChatArea messages={[]} onSend={onSend} isLoading={false} caseStatus="active" />)
    const textarea = screen.getByPlaceholderText(/type a message/i)
    fireEvent.change(textarea, { target: { value: 'Test message' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: false })
    expect(onSend).toHaveBeenCalledWith('Test message')
  })

  it('does not call onSend on Shift+Enter', () => {
    const onSend = vi.fn()
    render(<ChatArea messages={[]} onSend={onSend} isLoading={false} caseStatus="active" />)
    const textarea = screen.getByPlaceholderText(/type a message/i)
    fireEvent.change(textarea, { target: { value: 'Line 1' } })
    fireEvent.keyDown(textarea, { key: 'Enter', shiftKey: true })
    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables input and send button when case is complete', () => {
    render(<ChatArea messages={messages} onSend={vi.fn()} isLoading={false} caseStatus="complete" />)
    const textarea = screen.getByPlaceholderText(/case complete/i)
    expect(textarea).toBeDisabled()
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('disables send button when input is empty', () => {
    render(<ChatArea messages={[]} onSend={vi.fn()} isLoading={false} caseStatus="active" />)
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('shows loading indicator when isLoading is true', () => {
    render(<ChatArea messages={[]} onSend={vi.fn()} isLoading={true} caseStatus="active" />)
    // Loading bounce dots container should be present
    const { container } = render(<ChatArea messages={[]} onSend={vi.fn()} isLoading={true} caseStatus="active" />)
    expect(container.querySelector('.animate-bounce')).toBeInTheDocument()
  })

  it('shows case complete banner when caseStatus is complete', () => {
    render(<ChatArea messages={messages} onSend={vi.fn()} isLoading={false} caseStatus="complete" />)
    expect(screen.getByText(/all documents have been submitted/i)).toBeInTheDocument()
  })

  it('clears input after sending', () => {
    render(<ChatArea messages={[]} onSend={vi.fn()} isLoading={false} caseStatus="active" />)
    const textarea = screen.getByPlaceholderText(/type a message/i)
    fireEvent.change(textarea, { target: { value: 'Hello' } })
    fireEvent.click(screen.getByRole('button', { name: /send/i }))
    expect(textarea.value).toBe('')
  })
})
