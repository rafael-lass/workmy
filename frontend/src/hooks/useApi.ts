import { useCallback } from 'react'
import { useAuth } from './useAuth'
import { http } from '../lib/http'

type Options = {
  responseType?: 'json' | 'blob'
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  query?: Record<string, string | number | undefined | null>
}

export function useApi() {
  const { logout } = useAuth()
  const request = useCallback(async <T,>(path: string, options?: Options) => {
    try {
      return await http<T>(path, options)
    } catch (error) {
      if ((error as { status?: number }).status === 401) void logout()
      throw error
    }
  }, [logout])
  return { request }
}
