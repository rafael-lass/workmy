import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { AuthProvider } from './AuthContext'
import { useAuth } from '../hooks/useAuth'

function Probe() {
  const { user, loading } = useAuth()
  return <span>{loading ? 'validando' : user?.username ?? 'anônimo'}</span>
}

describe('AuthProvider', () => {
  it('valida a sessão pelo servidor e não depende de localStorage', async () => {
    localStorage.setItem('workmy_user', JSON.stringify({ username: 'cache-antigo' }))
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ id: 1, username: 'rafael', email: 'r@x.com' }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<AuthProvider><Probe /></AuthProvider>)
    expect(screen.getByText('validando')).toBeVisible()
    expect(await screen.findByText('rafael')).toBeVisible()
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/auth/me'), expect.objectContaining({ credentials: 'include' }))
  })
})
