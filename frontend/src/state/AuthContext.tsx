/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { http, ApiError } from '../lib/http'
import { waitForServer } from '../lib/readiness'
import type { User } from '../types'

type AuthContextData = {
  user: User | null
  isAuthenticated: boolean
  loading: boolean
  login: (identifier: string, password: string) => Promise<void>
  register: (payload: { username: string; email: string; password: string; telefone?: string }) => Promise<void>
  logout: () => Promise<void>
}

type BffAuthResponse = { user: User }
export const AuthContext = createContext<AuthContextData | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [serverError, setServerError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const cloud = import.meta.env.VITE_CLOUD_DEMO === 'true'

  useEffect(() => {
    let active = true
    const controller = new AbortController()
    setLoading(true)
    setServerError('')
    const ready = cloud ? waitForServer(controller.signal) : Promise.resolve()
    ready.then(() => http<User>('/auth/me'))
      .then((profile) => { if (active) setUser(profile) })
      .catch((error: unknown) => {
        if (!active) return
        setUser(null)
        if (cloud && !(error instanceof ApiError && error.status === 401)) {
          setServerError(error instanceof Error ? error.message : 'Servidor indisponível.')
        }
      })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false; controller.abort() }
  }, [cloud, attempt])

  const login = useCallback(async (identifier: string, password: string) => {
    const response = await http<BffAuthResponse>('/auth/login', { method: 'POST', body: { username: identifier, password } })
    setUser(response.user)
  }, [])

  const register = useCallback(async (payload: { username: string; email: string; password: string; telefone?: string }) => {
    const response = await http<BffAuthResponse>('/auth/register', { method: 'POST', body: payload })
    setUser(response.user)
  }, [])

  const logout = useCallback(async () => {
    try { await http<{ message: string }>('/auth/logout', { method: 'POST' }) } catch { /* estado local ainda precisa ser limpo */ }
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, isAuthenticated: Boolean(user), loading, login, register, logout }), [user, loading, login, register, logout])
  return <AuthContext.Provider value={value}>{cloud && (loading || serverError)
    ? <main className="auth-shell"><section className="auth-card" role="status">
        <p>{serverError || 'Iniciando o servidor de demonstração…'}</p>
        {!serverError && <p>A primeira conexão pode levar cerca de um minuto.</p>}
        {serverError && <button className="ui-button" onClick={() => setAttempt(current => current + 1)}>Tentar novamente</button>}
      </section></main>
    : children}</AuthContext.Provider>
}
