import { API_BASE_URL } from '../config'

export async function waitForServer(signal: AbortSignal, timeoutMs = 100_000): Promise<void> {
  const deadline = Date.now() + timeoutMs
  while (!signal.aborted && Date.now() < deadline) {
    const attempt = new AbortController()
    const abort = () => attempt.abort()
    signal.addEventListener('abort', abort, { once: true })
    const timer = setTimeout(abort, Math.min(10_000, deadline - Date.now()))
    try {
      const response = await fetch(`${API_BASE_URL}/health/ready`, {
        credentials: 'include', cache: 'no-store', signal: attempt.signal,
      })
      if (response.ok && response.headers.get('content-type')?.includes('application/json') &&
          (await response.json()).status === 'ready') return
    } catch { /* Only readiness GETs may be retried. */ }
    finally { clearTimeout(timer); signal.removeEventListener('abort', abort) }
    if (!signal.aborted && Date.now() < deadline) {
      await new Promise<void>((resolve) => {
        const done = () => { clearTimeout(delay); signal.removeEventListener('abort', done); resolve() }
        const delay = setTimeout(done, Math.min(2000, deadline - Date.now()))
        signal.addEventListener('abort', done, { once: true })
      })
    }
  }
  if (signal.aborted) throw new DOMException('Aborted', 'AbortError')
  throw new Error('O servidor está indisponível. Aguarde um pouco e tente novamente.')
}
