import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ManualPaymentDialog } from './FinanceDialogs'
import type { Projeto } from '../../types'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))

const project: Projeto = { id: 1, cliente_id: 1, cliente_nome: 'Ana', servico_id: 2, servico_nome: 'Site', valor_mensal: null, dia_vencimento: 5, recorrencia_inicio: null, criado_em: '', status: 'DISCOVERY', progresso: 0, tipo_recorrencia: 'AVULSO', valor: '100', ativo: false, total_acumulado: '0', possui_lancamentos: false }

describe('ManualPaymentDialog', () => {
  it('desabilita o envio e impede duplicação por clique repetido', () => {
    request.mockReturnValue(new Promise(() => undefined))
    render(<ManualPaymentDialog open projetos={[project]} onClose={vi.fn()} onSaved={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Projeto'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('Valor recebido'), { target: { value: '100' } })
    const submit = screen.getByRole('button', { name: 'Registrar como pago' })
    fireEvent.click(submit)
    fireEvent.click(submit)
    expect(request).toHaveBeenCalledTimes(1)
    expect(submit).toBeDisabled()
  })
})
