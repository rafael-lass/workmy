import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { TagSelector } from './TagSelector'
import { ServicoFormDialog } from './ServicoFormDialog'
import { ServicePdfDialog } from './ServicePresentationDialogs'
import type { Servico } from '../../types'

const request = vi.fn()
vi.mock('../../hooks/useApi', () => ({ useApi: () => ({ request }) }))
vi.mock('../../hooks/useAuth', () => ({ useAuth: () => ({ user: { username: 'Ana', email: 'ana@example.com' } }) }))
const service: Servico = { id: 1, nome: 'Site', tags: [], criado_em: '', descricao_documento: { version: 1, doc: { type: 'doc', content: [{ type: 'paragraph', content: [{ type: 'text', text: 'Descrição salva', marks: [{ type: 'bold' }] }] }] } } }

describe('Serviços', () => {
  beforeEach(() => { request.mockReset() })
  it('seleciona uma tag existente por Enter e cria uma nova sem duplicar envio', async () => {
    request.mockResolvedValueOnce([{ id: 1, nome: 'Web' }]).mockResolvedValueOnce({ id: 2, nome: 'Design' })
    const change = vi.fn()
    const user = userEvent.setup()
    render(<TagSelector selected={[]} onChange={change} disabled={false} onBusyChange={vi.fn()} />)
    await screen.findByRole('button', { name: 'Web' })
    const input = screen.getByPlaceholderText('Pesquisar ou criar uma tag')
    await user.type(input, 'web{Enter}')
    expect(change).toHaveBeenCalledWith([{ id: 1, nome: 'Web' }])
    await user.type(input, 'Design{Enter}')
    await waitFor(() => expect(change).toHaveBeenCalledWith([{ id: 2, nome: 'Design' }]))
    expect(request).toHaveBeenCalledTimes(2)
  })
  it('reabre formatação salva, valida nome e preserva formulário após falha', async () => {
    request.mockResolvedValueOnce([]).mockRejectedValueOnce(new Error('Falha de rede'))
    const close = vi.fn()
    const user = userEvent.setup()
    render(<ServicoFormDialog open servico={service} onClose={close} onSaved={vi.fn()} />)
    expect(screen.getByRole('textbox', { name: 'Descrição formatada' }).querySelector('strong')).toHaveTextContent('Descrição salva')
    expect(screen.queryByLabelText('Repositório')).not.toBeInTheDocument()
    await user.clear(screen.getByLabelText('Nome'))
    await user.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(screen.getByText('Informe o nome do serviço.')).toBeVisible()
    await user.type(screen.getByLabelText('Nome'), 'Novo nome')
    await user.click(screen.getByRole('button', { name: 'Salvar alterações' }))
    expect(await screen.findByText('Falha de rede')).toBeVisible()
    expect(screen.getByLabelText('Nome')).toHaveValue('Novo nome')
    expect(close).not.toHaveBeenCalled()
  })
  it('bloqueia exportação duplicada e preserva contatos se a API falha', async () => {
    let reject!: (error: Error) => void
    request.mockImplementation(() => new Promise((_resolve, failure) => { reject = failure }))
    render(<ServicePdfDialog service={service} onClose={vi.fn()} />)
    const form = screen.getByLabelText('Nome profissional').closest('form')!
    fireEvent.submit(form); fireEvent.submit(form)
    expect(request).toHaveBeenCalledTimes(1)
    expect(request).toHaveBeenCalledWith('/servicos/1/pdf', expect.objectContaining({ responseType: 'blob', body: { nome_profissional: 'Ana', email: 'ana@example.com', telefone: null } }))
    reject(new Error('Sessão expirada'))
    expect(await screen.findByText('Sessão expirada')).toBeVisible()
    expect(screen.getByLabelText('Nome profissional')).toHaveValue('Ana')
  })
})
