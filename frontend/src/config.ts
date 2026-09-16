function resolveApiBaseUrl(): string {
  const fromEnv = import.meta.env.VITE_API_BASE_URL
  if (fromEnv) return String(fromEnv).replace(/\/+$/, '')

  // Local dev apenas — redireciona para o BFF Proxy Gateway
  if (import.meta.env.DEV) return '/api'

  if (import.meta.env.PROD) {
    console.error(
      '[WorkMy] VITE_API_BASE_URL não definida no build de produção. Configure no painel Vercel.',
    )
  }
  return ''
}

export const API_BASE_URL = resolveApiBaseUrl()
