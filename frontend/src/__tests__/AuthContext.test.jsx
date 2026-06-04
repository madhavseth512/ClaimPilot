import { render, screen, act } from '@testing-library/react'
import { describe, it, expect, beforeEach } from 'vitest'
import { AuthProvider, AuthContext } from '../context/AuthContext'
import { useContext } from 'react'

function Consumer() {
  const ctx = useContext(AuthContext)
  return (
    <div>
      <span data-testid="auth">{ctx.isAuthenticated ? 'yes' : 'no'}</span>
      <span data-testid="user">{ctx.user?.name || 'none'}</span>
      <button onClick={() => ctx.signIn('tok123', { name: 'Alice', email: 'a@b.com' })}>Login</button>
      <button onClick={() => ctx.signOut()}>Logout</button>
    </div>
  )
}

describe('AuthContext', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('is not authenticated initially', () => {
    render(<AuthProvider><Consumer /></AuthProvider>)
    expect(screen.getByTestId('auth').textContent).toBe('no')
  })

  it('becomes authenticated after signIn', () => {
    render(<AuthProvider><Consumer /></AuthProvider>)
    act(() => { screen.getByText('Login').click() })
    expect(screen.getByTestId('auth').textContent).toBe('yes')
    expect(screen.getByTestId('user').textContent).toBe('Alice')
  })

  it('persists token in localStorage after signIn', () => {
    render(<AuthProvider><Consumer /></AuthProvider>)
    act(() => { screen.getByText('Login').click() })
    expect(localStorage.getItem('token')).toBe('tok123')
  })

  it('clears localStorage after signOut', () => {
    render(<AuthProvider><Consumer /></AuthProvider>)
    act(() => { screen.getByText('Login').click() })
    act(() => { screen.getByText('Logout').click() })
    expect(localStorage.getItem('token')).toBeNull()
    expect(screen.getByTestId('auth').textContent).toBe('no')
  })

  it('reads existing token from localStorage on mount', () => {
    localStorage.setItem('token', 'existing-token')
    localStorage.setItem('user', JSON.stringify({ name: 'Bob', email: 'b@b.com' }))
    render(<AuthProvider><Consumer /></AuthProvider>)
    expect(screen.getByTestId('auth').textContent).toBe('yes')
    expect(screen.getByTestId('user').textContent).toBe('Bob')
  })
})
