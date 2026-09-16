import { API_BASE_URL } from '../config'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

// ---------------------------------------------------------------------------
// C6 FIX: O cliente HTTP nunca envia Authorization: Bearer.
// Os tokens JWT ficam em cookies HTTP-Only gerenciados pelo BFF.
// O navegador envia os cookies automaticamente via credentials: 'include'.
// ---------------------------------------------------------------------------

const normalizeBody = (body: unknown) => {
  if (!body || typeof body !== 'object') return undefined
  const form = new URLSearchParams()
  Object.entries(body as Record<string, unknown>).forEach(([key, value]) => {
    if (value === undefined || value === null) return
    form.append(key, String(value))
  })
  return form
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

function extractErrorMessage(payload: unknown): string | null {
  if (!payload) return null
  if (typeof payload === 'string') return payload
  if (Array.isArray(payload)) {
    for (const item of payload) {
      const nested = extractErrorMessage(item)
      if (nested) return nested
    }
    return null
  }
  if (typeof payload === 'object') {
    const obj = payload as Record<string, unknown>
    if (typeof obj.detail === 'string') return obj.detail
    if (obj.detail) {
      const nested = extractErrorMessage(obj.detail)
      if (nested) return nested
    }
    if (typeof obj.msg === 'string') return obj.msg
    if (typeof obj.message === 'string') return obj.message
    for (const value of Object.values(obj)) {
      const nested = extractErrorMessage(value)
      if (nested) return nested
    }
  }
  return null
}

export async function http<T>(
  path: string,
  options?: {
    method?: HttpMethod
    responseType?: 'json' | 'blob'
    body?: unknown
    query?: Record<string, string | number | undefined | null>
  },
): Promise<T> {
  const method = options?.method ?? 'GET'
  const query = options?.query
    ? `?${new URLSearchParams(
        Object.entries(options.query)
          .filter(([, v]) => v !== undefined && v !== null)
          .map(([k, v]) => [k, String(v)]),
      ).toString()}`
    : ''

  const url = `${API_BASE_URL}${path}${query}`
  const headers: Record<string, string> = {}

  let body: BodyInit | undefined
  if (options?.body) {
    if (method === 'POST' || method === 'PATCH' || method === 'PUT') {
      body = JSON.stringify(options.body)
      headers['Content-Type'] = 'application/json'
    } else {
      body = normalizeBody(options.body)
      headers['Content-Type'] = 'application/x-www-form-urlencoded'
    }
  }

  const res = await fetch(url, {
    method,
    headers,
    body,
    credentials: 'include', // Envia cookies HTTP-Only automaticamente (gerenciados pelo BFF)
  })

  if (res.ok && options?.responseType === 'blob') return await res.blob() as T
  let data: unknown = null
  try {
    data = await res.json()
  } catch {
    data = null
  }

  if (!res.ok) {
    const message = extractErrorMessage(data) ?? `Erro ${res.status} ao acessar a API`
    throw new ApiError(message, res.status)
  }

  return data as T
}
