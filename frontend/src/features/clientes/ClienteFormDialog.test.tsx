import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ClienteFormDialog } from './ClienteFormDialog'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))

describe('ClienteFormDialog', () => {
  beforeEach(() => request.mockReset())

  it('mostra erros próximos aos campos inválidos sem chamar a API', async () => {
    const user = userEvent.setup()
    render(<ClienteFormDialog open onClose={vi.fn()} onSaved={vi.fn()} />)
    await user.type(screen.getByLabelText(/E-mail/), 'email-invalido')
    await user.click(screen.getByRole('button', { name: 'Criar cliente' }))
    expect(screen.getByText('Informe o nome do cliente.')).toBeVisible()
    expect(screen.getByText('Informe um e-mail válido.')).toBeVisible()
    expect(request).not.toHaveBeenCalled()
  })

  it('mantém o diálogo aberto quando a API falha', async () => {
    request.mockRejectedValueOnce(new Error('falha'))
    const user = userEvent.setup()
    render(<ClienteFormDialog open onClose={vi.fn()} onSaved={vi.fn()} />)
    await user.type(screen.getByLabelText('Nome'), 'Ana')
    fireEvent.submit(document.getElementById('cliente-form')!)
    expect(await screen.findByText('Não foi possível salvar o cliente.')).toBeVisible()
    expect(screen.getByRole('dialog')).toHaveAttribute('open')
  })
})
