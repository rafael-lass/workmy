import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ManualPaymentDialog } from './FinanceDialogs'
import type { Projeto } from '../../types'
import * as image from '../../lib/image'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))
beforeEach(() => { request.mockReset() })

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

it('explica a falta de projetos disponíveis e oferece o próximo passo', () => {
  const create = vi.fn()
  render(<ManualPaymentDialog open projetos={[{ ...project, status: 'ARCHIVED' }]} onCreateProject={create} onClose={vi.fn()} onSaved={vi.fn()} />)
  expect(screen.getByText(/Nenhum projeto disponível para recebimento/)).toBeVisible()
  expect(screen.getByLabelText('Serviço')).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Registrar como pago' })).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: 'Ir para projetos' }))
  expect(create).toHaveBeenCalledOnce()
  expect(request).not.toHaveBeenCalled()
})

it('distingue carregamento de erro e permite tentar novamente dentro do modal', () => {
  const retry = vi.fn()
  const props = { open: true, projetos: [project], onRetry: retry, onClose: vi.fn(), onSaved: vi.fn() }
  const { rerender } = render(<ManualPaymentDialog {...props} loading />)
  expect(screen.getByText(/Carregando os projetos/)).toBeVisible()
  expect(screen.getByRole('button', { name: 'Registrar como pago' })).toBeDisabled()
  rerender(<ManualPaymentDialog {...props} loadError="Falha ao carregar os projetos" />)
  expect(screen.getByText('Falha ao carregar os projetos')).toBeVisible()
  fireEvent.click(screen.getByRole('button', { name: 'Tentar novamente' }))
  expect(retry).toHaveBeenCalledOnce()
  expect(screen.getByLabelText('Serviço')).toBeDisabled()
})

it('espera os projetos iniciais e preserva o formulário durante atualização de dados', () => {
  const props = { open: true, defaultProjectId: 1, onClose: vi.fn(), onSaved: vi.fn() }
  const { rerender } = render(<ManualPaymentDialog {...props} projetos={[]} loading />)
  rerender(<ManualPaymentDialog {...props} projetos={[project]} />)
  expect(screen.getByLabelText('Cliente')).toHaveValue('1')
  fireEvent.change(screen.getByLabelText('Valor recebido'), { target: { value: '75' } })
  rerender(<ManualPaymentDialog {...props} projetos={[{ ...project }]} loading />)
  rerender(<ManualPaymentDialog {...props} projetos={[{ ...project }]} />)
  expect(screen.getByLabelText('Cliente')).toHaveValue('1')
  expect(screen.getByLabelText('Valor recebido')).toHaveValue(75)
})

it('aguarda a leitura do comprovante antes de enviar o recebimento', async () => {
  let finish!: (value: string) => void
  vi.spyOn(image, 'readReceiptDataUrl').mockReturnValue(new Promise(resolve => { finish = resolve }))
  request.mockResolvedValue({ id: 1 })
  render(<ManualPaymentDialog open projetos={[project]} defaultProjectId={1} onClose={vi.fn()} onSaved={vi.fn()} />)
  fireEvent.change(screen.getByLabelText('Valor recebido'), { target: { value: '100' } })
  fireEvent.change(screen.getByLabelText(/Comprovante/), { target: { files: [new File(['test'], 'recibo.pdf', { type: 'application/pdf' })] } })
  const submit = screen.getByRole('button', { name: 'Registrar como pago' })
  expect(submit).toBeDisabled()
  fireEvent.submit(document.getElementById('manual-payment-form')!)
  expect(request).not.toHaveBeenCalled()
  await act(async () => finish('data:application/pdf;base64,dGVzdA=='))
  fireEvent.click(submit)
  expect(request).toHaveBeenCalledWith('/pagamentos/', expect.objectContaining({ body: expect.objectContaining({ comprovante_base64: 'data:application/pdf;base64,dGVzdA==' }) }))
})
