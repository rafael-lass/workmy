import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { vi, it, expect, beforeEach } from 'vitest'
import { DashboardExport } from './DashboardExport'

const { request } = vi.hoisted(() => ({ request: vi.fn() }))
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))
beforeEach(() => {
  request.mockReset()
  URL.createObjectURL = vi.fn(() => 'blob:test')
  URL.revokeObjectURL = vi.fn()
  vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
})

it('envia período sem paginação e bloqueia exportações duplicadas', async () => {
  let finish!: (value: Blob) => void
  request.mockReturnValue(new Promise<Blob>(resolve => { finish = resolve }))
  render(<DashboardExport />)
  fireEvent.change(screen.getByLabelText('Período da exportação'), { target: { value: 'total' } })
  fireEvent.click(screen.getByRole('button', { name: 'Baixar planilhas' }))
  expect(request).toHaveBeenCalledWith('/dashboard/exportar.zip', { responseType: 'blob', query: { periodo: 'total' } })
  expect(screen.getByRole('button', { name: 'Gerando planilhas…' })).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: 'Gerando planilhas…' }))
  expect(request).toHaveBeenCalledTimes(1)
  finish(new Blob(['xlsx']))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Baixar planilhas' })).toBeEnabled())
  expect(URL.createObjectURL).toHaveBeenCalled()
})

it('preserva período e libera nova tentativa após falha', async () => {
  request.mockRejectedValueOnce(new Error('network')).mockResolvedValueOnce(new Blob(['xlsx']))
  render(<DashboardExport />)
  fireEvent.change(screen.getByLabelText('Período da exportação'), { target: { value: '12' } })
  fireEvent.click(screen.getByRole('button', { name: 'Baixar planilhas' }))
  expect(await screen.findByText('Não foi possível exportar o Excel. Tente novamente.')).toBeInTheDocument()
  expect(screen.getByLabelText('Período da exportação')).toHaveValue('12')
  fireEvent.click(screen.getByRole('button', { name: 'Baixar planilhas' }))
  await waitFor(() => expect(request).toHaveBeenCalledTimes(2))
})
