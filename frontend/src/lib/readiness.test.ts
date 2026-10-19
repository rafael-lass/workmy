import { afterEach, expect, it, vi } from 'vitest'
import { waitForServer } from './readiness'

afterEach(() => { vi.unstubAllGlobals(); vi.useRealTimers() })
it('retries HTML and 503 until ready, without sending a mutation', async () => {
  vi.useFakeTimers()
  const fetcher = vi.fn()
    .mockResolvedValueOnce(new Response('<html>starting</html>', { headers: { 'Content-Type': 'text/html' } }))
    .mockResolvedValueOnce(new Response('{}', { status: 503, headers: { 'Content-Type': 'application/json' } }))
    .mockResolvedValueOnce(new Response('{"status":"ready"}', { headers: { 'Content-Type': 'application/json' } }))
  vi.stubGlobal('fetch', fetcher)
  const result = waitForServer(new AbortController().signal)
  await vi.advanceTimersByTimeAsync(4000)
  await result
  expect(fetcher).toHaveBeenCalledTimes(3)
  expect(fetcher.mock.calls.every(([url, opts]) => url.endsWith('/health/ready') && !opts.method)).toBe(true)
})
it('stops on cancellation', async () => {
  const controller = new AbortController()
  controller.abort()
  await expect(waitForServer(controller.signal)).rejects.toMatchObject({ name: 'AbortError' })
})
it('reports unavailability when the deadline expires', async () => {
  await expect(waitForServer(new AbortController().signal, 0)).rejects.toThrow('indisponível')
})
