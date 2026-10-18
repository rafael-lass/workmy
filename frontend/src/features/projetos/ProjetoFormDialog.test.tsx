import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ProjetoFormDialog } from './ProjetoFormDialog'
import type { Projeto } from '../../types'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))

describe('ProjetoFormDialog', () => {
  it('edita a etapa sem progresso e sem oferecer arquivamento como etapa', async () => {
    const user = userEvent.setup()
    const projeto: Projeto = { id: 1, cliente_id: 1, cliente_nome: 'Ana', servico_id: 2, servico_nome: 'Site', valor_mensal: null, dia_vencimento: 5, recorrencia_inicio: null, criado_em: '', status: 'REVIEW', tipo_recorrencia: 'AVULSO', valor: '100', ativo: false, total_acumulado: '0', possui_lancamentos: false }
    request.mockResolvedValue({ ...projeto, status: 'COMPLETED' })
    render(<ProjetoFormDialog open projeto={projeto} clientes={[{ id: 1, nome: 'Ana', empresa: 'ACME', total_acumulado: '0', criado_em: '' }]} servicos={[{ id: 2, nome: 'Site', tags: [], criado_em: '' }]} onClose={vi.fn()} onSaved={vi.fn()} />)
    expect(screen.queryByLabelText('Progresso')).not.toBeInTheDocument()
    expect(screen.queryByRole('option', { name: 'Arquivado' })).not.toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Revisão' })).toBeVisible()
    expect(screen.getByRole('option', { name: 'Andamento' })).toBeVisible()
    await user.selectOptions(screen.getByLabelText('Etapa'), 'COMPLETED')
    await user.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(request).toHaveBeenCalledWith('/projetos/1', { method: 'PUT', body: { status: 'COMPLETED', valor: 100 } })
    request.mockClear()
  })
  it('exige os campos de recorrência apenas no modelo mensal', async () => {
    const user = userEvent.setup()
    render(<ProjetoFormDialog open clientes={[{ id: 1, nome: 'Ana', empresa: 'ACME', total_acumulado: '0', criado_em: '' }]} servicos={[{ id: 2, nome: 'Site', tags: [], criado_em: '' }]} onClose={vi.fn()} onSaved={vi.fn()} />)
    await user.selectOptions(screen.getByLabelText('Cliente'), '1')
    await user.selectOptions(screen.getByLabelText('Serviço'), '2')
    await user.selectOptions(screen.getByLabelText('Modelo de cobrança'), 'MENSAL')
    expect(screen.getByLabelText('Valor mensal')).toBeVisible()
    expect(screen.getByLabelText('Início da recorrência')).toBeVisible()
    await user.click(screen.getByRole('button', { name: 'Criar projeto' }))
    expect(screen.getByText('Informe o valor mensal.')).toBeVisible()
    expect(screen.getByText('Informe a data inicial.')).toBeVisible()
    expect(request).not.toHaveBeenCalled()
  })
})
