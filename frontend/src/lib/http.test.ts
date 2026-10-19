import { afterEach, expect, it, vi } from 'vitest'
import { http } from './http'

afterEach(() => vi.unstubAllGlobals())
it('downloads binary responses without trying JSON', async () => {
  const blob = new Blob(['%PDF-test'], { type: 'application/pdf' })
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, headers: new Headers({ 'Content-Type': 'application/pdf' }), blob: () => Promise.resolve(blob) }))
  expect(await http('/servicos/1/pdf', { method: 'POST', responseType: 'blob' })).toBe(blob)
})
it('preserves JSON authentication errors during downloads', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 401, headers: new Headers(), json: () => Promise.resolve({ detail: 'Sessão expirada' }) }))
  await expect(http('/servicos/1/pdf', { responseType: 'blob' })).rejects.toMatchObject({ status: 401, message: 'Sessão expirada' })
})
it('does not download a provider HTML page as ZIP', async () => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>Starting</html>', { headers: { 'Content-Type': 'text/html' } })))
  await expect(http('/dashboard/exportar.zip', { responseType: 'blob' })).rejects.toMatchObject({ status: 503 })
})
