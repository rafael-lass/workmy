import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { PaymentActions } from './FinanceiroPage'
import type { Pagamento } from '../types'

const base: Pagamento = { id: 1, projeto_id: 1, cliente_id: 1, projeto_cliente_nome: 'Ana', projeto_servico_nome: 'Site', valor: '100.00', tipo_pagamento: 'MENSAL', tipo_pagamento_display: 'Mensalidade', status: 'PENDENTE', em_atraso: false, data_vencimento: '2026-09-01', gerado_automaticamente: true, status_alterado_em: '', criado_em: '', atualizado_em: '' }
const handlers = { onReceive: vi.fn(), onAdjust: vi.fn(), onDetails: vi.fn(), onReceipt: vi.fn() }

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
