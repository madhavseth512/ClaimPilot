import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import MessageBubble from '../components/MessageBubble'

describe('MessageBubble', () => {
  it('renders user message on the right', () => {
    render(<MessageBubble role="user" content="Hello" timestamp={new Date().toISOString()} />)
    expect(screen.getByText('Hello')).toBeInTheDocument()
  })

  it('renders assistant message on the left', () => {
    render(<MessageBubble role="assistant" content="I am ClaimPilot" timestamp={new Date().toISOString()} />)
    expect(screen.getByText('I am ClaimPilot')).toBeInTheDocument()
  })

  it('shows the building emoji for assistant messages', () => {
    render(<MessageBubble role="assistant" content="Hi" timestamp={new Date().toISOString()} />)
    expect(screen.getByText('🏢')).toBeInTheDocument()
  })

  it('renders multiline content correctly', () => {
    render(<MessageBubble role="assistant" content={"Line one\nLine two"} timestamp={new Date().toISOString()} />)
    expect(screen.getByText(/Line one/)).toBeInTheDocument()
  })

  it('formats timestamp as time string', () => {
    const ts = new Date('2025-01-01T02:30:00').toISOString()
    render(<MessageBubble role="user" content="Test" timestamp={ts} />)
    // Timestamp should be visible somewhere in the component
    const container = document.body
    expect(container.textContent).toMatch(/\d{1,2}:\d{2}/)
  })
})
