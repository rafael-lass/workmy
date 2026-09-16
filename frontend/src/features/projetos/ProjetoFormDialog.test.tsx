import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { ProjetoFormDialog } from './ProjetoFormDialog'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))

describe('ProjetoFormDialog', () => {
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
