import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { FinanceiroPage, PaymentActions } from './FinanceiroPage'
import { MemoryRouter } from 'react-router-dom'
import type { Pagamento } from '../types'

const base: Pagamento = { id: 1, projeto_id: 1, cliente_id: 1, projeto_cliente_nome: 'Ana', projeto_servico_nome: 'Site', valor: '100.00', tipo_pagamento: 'MENSAL', tipo_pagamento_display: 'Mensalidade', status: 'PENDENTE', em_atraso: false, data_vencimento: '2026-09-01', gerado_automaticamente: true, status_alterado_em: '', criado_em: '', atualizado_em: '' }
const handlers = { onReceive: vi.fn(), onAdjust: vi.fn(), onDetails: vi.fn(), onReceipt: vi.fn() }
const request = vi.fn()
vi.mock('../hooks/useApi', () => ({ useApi: () => ({ request }) }))
vi.mock('../shared/ui/Toast', () => ({ useToast: () => ({ notify: vi.fn() }) }))

describe('ações financeiras por estado', () => {
  it('oferece receber/cancelar somente para pendências', () => {
    render(<PaymentActions payment={base} {...handlers} />)
    expect(screen.getByRole('button', { name: /Receber/ })).toBeVisible()
    expect(screen.getByRole('button', { name: 'Cancelar' })).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Estornar' })).not.toBeInTheDocument()
  })

  it('oferece estorno somente para pagamentos confirmados', () => {
    render(<PaymentActions payment={{ ...base, status: 'PAGO' }} {...handlers} />)
    expect(screen.getByRole('button', { name: 'Estornar' })).toBeVisible()
    expect(screen.queryByRole('button', { name: /Receber/ })).not.toBeInTheDocument()
  })
})

it('ignora respostas antigas quando filtros mudam em uma conexão lenta', async () => {
  let finishOld!: (value: unknown) => void
  let finishNew!: (value: unknown) => void
  const list = (name: string) => ({ items: [{ ...base, projeto_cliente_nome: name }], total: 1, page: 1, page_size: 10 })
  request.mockImplementation((path: string, options?: { query?: { q?: string } }) => {
    if (path === '/dashboard/resumo') return Promise.resolve({ recebido_mes: '0', pendente_total: '0', atrasado_total: '0' })
    if (path !== '/pagamentos/') return Promise.resolve([])
    if (options?.query?.q === 'antigo') return new Promise(resolve => { finishOld = resolve })
    if (options?.query?.q === 'novo') return new Promise(resolve => { finishNew = resolve })
    return Promise.resolve(list('Inicial'))
  })
  render(<MemoryRouter><FinanceiroPage /></MemoryRouter>)
  await screen.findByRole('heading', { name: 'Financeiro' })
  fireEvent.change(screen.getByLabelText('Buscar lançamentos'), { target: { value: 'antigo' } })
  fireEvent.change(screen.getByLabelText('Buscar lançamentos'), { target: { value: 'novo' } })
  await act(async () => finishNew(list('Resultado novo')))
  await waitFor(() => expect(screen.getAllByText('Resultado novo')).toHaveLength(2))
  await act(async () => finishOld(list('Resultado antigo')))
  expect(screen.queryByText('Resultado antigo')).not.toBeInTheDocument()
  expect(screen.getAllByText('Resultado novo')).toHaveLength(2)
})
