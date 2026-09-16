import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { DashboardPage } from './DashboardPage'

const request = vi.fn().mockResolvedValue({ recebido_mes: '0', pendente_total: '0', atrasado_total: '0', previsto_proximo_mes: '0', projetos_ativos: 0, clientes_total: 0, serie_seis_meses: [], ultimos_recebimentos: [] })
vi.mock('../hooks/useApi', () => ({ useApi: () => ({ request }) }))

function LocationProbe() {
  const location = useLocation()
  return <span>{location.pathname}{location.search}</span>
}

describe('ações rápidas do dashboard', () => {
  it('leva ao formulário canônico de projeto pela URL', async () => {
    const user = userEvent.setup()
    render(<MemoryRouter initialEntries={['/dashboard']}><Routes><Route path="/dashboard" element={<DashboardPage />} /><Route path="/projetos" element={<LocationProbe />} /></Routes></MemoryRouter>)
    await user.click(await screen.findByRole('button', { name: /Novo projeto/ }))
    expect(screen.getByText('/projetos?acao=novo')).toBeVisible()
  })
})
