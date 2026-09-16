/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { http } from '../lib/http'
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

  useEffect(() => {
    let active = true
    http<User>('/auth/me')
      .then((profile) => { if (active) setUser(profile) })
      .catch(() => { if (active) setUser(null) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [])

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
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
