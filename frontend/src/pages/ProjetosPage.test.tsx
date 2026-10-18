import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { expect, it, vi } from 'vitest'
import { ProjetosPage } from './ProjetosPage'
import { AppLayout } from '../components/AppLayout'
import type { Projeto } from '../types'

const request = vi.fn()
const notify = vi.fn()
vi.mock('../hooks/useApi', () => ({ useApi: () => ({ request }) }))
vi.mock('../hooks/useAuth', () => ({ useAuth: () => ({ user: { username: 'Rafael', email: 'teste@example.com' }, logout: vi.fn() }) }))
vi.mock('../shared/ui/Toast', () => ({ useToast: () => ({ notify }) }))

it('navbar mantém navegação sem o botão Novo projeto', () => {
  render(<MemoryRouter><AppLayout /></MemoryRouter>)
  expect(screen.queryByRole('button', { name: 'Novo projeto' })).not.toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Projetos' })).toHaveAttribute('href', '/projetos')
})

it('arquiva com confirmação, mantém exclusão nos dois layouts e não retoma finalizados', async () => {
  const user = userEvent.setup()
  const project: Projeto = { id: 1, cliente_id: 1, cliente_nome: 'Ana', servico_id: 2, servico_nome: 'Site', valor_mensal: '100', dia_vencimento: 5, recorrencia_inicio: '2026-09-01', criado_em: '', status: 'COMPLETED', tipo_recorrencia: 'MENSAL', valor: '100', ativo: false, total_acumulado: '100', possui_lancamentos: true }
  request.mockImplementation(async (url: string) => url === '/projetos/' ? [project] : url === '/projetos/1/status' ? { ...project, status: 'ARCHIVED' } : [])
  render(<MemoryRouter><ProjetosPage /></MemoryRouter>)
  expect(await screen.findAllByText('Finalizado', { selector: 'span' })).toHaveLength(2)
  expect(screen.queryByText('Progresso')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Retomar' })).not.toBeInTheDocument()
  const deletes = screen.getAllByRole('button', { name: 'Excluir' })
  expect(deletes).toHaveLength(2)
  deletes.forEach(button => expect(button).toBeDisabled())
  await user.click(screen.getAllByRole('button', { name: 'Arquivar' })[0])
  expect(request).not.toHaveBeenCalledWith('/projetos/1/status', expect.anything())
  await user.click(screen.getByRole('button', { name: 'Arquivar projeto' }))
  expect(request).toHaveBeenCalledWith('/projetos/1/status', { method: 'PATCH', body: { status: 'ARCHIVED' } })
  await user.selectOptions(screen.getByLabelText('Situação do projeto'), 'archived')
  expect(await screen.findAllByText('Arquivado', { selector: 'span' })).toHaveLength(2)
  expect(within(screen.getByLabelText('Filtrar etapa')).queryByRole('option', { name: 'Arquivado' })).not.toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: 'Reativar' })).toHaveLength(2)
  await user.selectOptions(screen.getByLabelText('Situação do projeto'), 'all')
  expect(screen.getAllByRole('button', { name: 'Reativar' })).toHaveLength(2)
  expect(screen.getByLabelText('Filtrar etapa')).toBeEnabled()
})


it('reativa arquivado em Planejamento com recorrência pausada e permite excluir sem histórico', async () => {
  const user = userEvent.setup()
  const project: Projeto = { id: 1, cliente_id: 1, cliente_nome: 'Ana', servico_id: 2, servico_nome: 'Site', valor_mensal: '100', dia_vencimento: 5, recorrencia_inicio: '2026-09-01', criado_em: '', status: 'ARCHIVED', tipo_recorrencia: 'MENSAL', valor: '100', ativo: false, total_acumulado: '0', possui_lancamentos: false }
  request.mockClear()
  request.mockImplementation(async (url: string) => url === '/projetos/' ? [project] : url === '/projetos/1/status' ? { ...project, status: 'DISCOVERY' } : [])
  render(<MemoryRouter><ProjetosPage /></MemoryRouter>)
  await screen.findByLabelText('Situação do projeto')
  await user.selectOptions(screen.getByLabelText('Situação do projeto'), 'archived')
  screen.getAllByRole('button', { name: 'Excluir' }).forEach(button => expect(button).toBeEnabled())
  await user.click(screen.getAllByRole('button', { name: 'Reativar' })[0])
  await user.click(screen.getByRole('button', { name: 'Reativar projeto' }))
  expect(request).toHaveBeenCalledWith('/projetos/1/status', { method: 'PATCH', body: { status: 'DISCOVERY' } })
  expect(await screen.findAllByText('Planejamento', { selector: 'span' })).toHaveLength(2)
  expect(screen.getAllByRole('button', { name: 'Retomar' })).toHaveLength(2)
  await user.click(screen.getAllByRole('button', { name: 'Excluir' })[0])
  await user.click(screen.getByRole('button', { name: 'Excluir projeto' }))
  expect(request).toHaveBeenCalledWith('/projetos/1', { method: 'DELETE' })
})
