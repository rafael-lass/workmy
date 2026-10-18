import { fireEvent, render, screen, within } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { ManualPaymentDialog } from './FinanceDialogs'
import type { Projeto } from '../../types'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))

const project: Projeto = { id: 1, cliente_id: 1, cliente_nome: 'Ana', servico_id: 2, servico_nome: 'Site', valor_mensal: null, dia_vencimento: 5, recorrencia_inicio: null, criado_em: '', status: 'DISCOVERY', tipo_recorrencia: 'AVULSO', valor: '100', ativo: false, total_acumulado: '0', possui_lancamentos: false }

describe('ManualPaymentDialog', () => {
  it('desabilita o envio e impede duplicação por clique repetido', () => {
    request.mockReturnValue(new Promise(() => undefined))
    render(<ManualPaymentDialog open projetos={[project]} onClose={vi.fn()} onSaved={vi.fn()} />)
    fireEvent.change(screen.getByLabelText('Serviço'), { target: { value: '2' } })
    fireEvent.change(screen.getByLabelText('Cliente'), { target: { value: '1' } })
    fireEvent.change(screen.getByLabelText('Valor recebido'), { target: { value: '100' } })
    const submit = screen.getByRole('button', { name: 'Registrar como pago' })
    fireEvent.click(submit)
    fireEvent.click(submit)
    expect(request).toHaveBeenCalledTimes(1)
    expect(submit).toBeDisabled()
  })
})


it('filtra clientes pelo serviço e limpa a escolha ao trocar o serviço', () => {
  request.mockClear()
  const projects: Projeto[] = [project, { ...project, id: 2, cliente_id: 2, cliente_nome: 'Bruno' }, { ...project, id: 3, servico_id: 3, servico_nome: 'Suporte', cliente_nome: 'Carla' }, { ...project, id: 4, servico_id: 4, servico_nome: 'Arquivado', status: 'ARCHIVED' }]
  render(<ManualPaymentDialog open projetos={projects} onClose={vi.fn()} onSaved={vi.fn()} />)
  const service = screen.getByLabelText('Serviço')
  const client = screen.getByLabelText('Cliente')
  expect(client).toBeDisabled()
  expect(within(service).getAllByRole('option')).toHaveLength(3)
  fireEvent.change(service, { target: { value: '2' } })
  expect(within(client).getByRole('option', { name: 'Bruno' })).toBeInTheDocument()
  expect(within(client).queryByRole('option', { name: 'Carla' })).not.toBeInTheDocument()
  fireEvent.change(client, { target: { value: '2' } })
  fireEvent.change(service, { target: { value: '3' } })
  expect(client).toHaveValue('')
  fireEvent.change(screen.getByLabelText('Valor recebido'), { target: { value: '100' } })
  fireEvent.click(screen.getByRole('button', { name: 'Registrar como pago' }))
  expect(request).not.toHaveBeenCalled()
  fireEvent.change(client, { target: { value: '3' } })
  fireEvent.click(screen.getByRole('button', { name: 'Registrar como pago' }))
  expect(request).toHaveBeenCalledWith('/pagamentos/', expect.objectContaining({ body: expect.objectContaining({ projeto_id: 3 }) }))
})

it('preenche serviço e cliente do projeto recebido por contexto', () => {
  render(<ManualPaymentDialog open projetos={[project]} defaultProjectId={1} onClose={vi.fn()} onSaved={vi.fn()} />)
  expect(screen.getByLabelText('Serviço')).toHaveValue('2')
  expect(screen.getByLabelText('Cliente')).toHaveValue('1')
})
