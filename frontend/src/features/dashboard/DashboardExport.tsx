import { useRef, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import { ApiError } from '../../lib/http'
import { Button } from '../../shared/ui/Button'
import { Alert } from '../../shared/ui/Alert'

export function DashboardExport() {
  const { request } = useApi()
  const [period, setPeriod] = useState('3')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const pending = useRef(false)
  const now = new Date()
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: 'America/Sao_Paulo', year: 'numeric', month: '2-digit', day: '2-digit' }).format(now)
  const [year, month] = today.split('-').map(Number)
  const start = new Date(Date.UTC(year, month - Number(period), 1))
  const label = period === 'total' ? 'Todo o histórico e todos os cadastros da conta.' : `Vencimentos de ${start.toLocaleDateString('pt-BR', { timeZone: 'UTC' })} até ${today.split('-').reverse().join('/')}. Inclui os cadastros relacionados.`

  async function download() {
    if (pending.current) return
    pending.current = true; setBusy(true); setError('')
    try {
      const blob = await request<Blob>('/dashboard/exportar.zip', { responseType: 'blob', query: { periodo: period } })
      const url = URL.createObjectURL(blob)
      try {
        const anchor = document.createElement('a')
        anchor.href = url; anchor.download = `workmy-relatorios-${period}-${today}.zip`
        document.body.append(anchor); anchor.click(); anchor.remove()
      } finally { window.setTimeout(() => URL.revokeObjectURL(url), 1000) }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Não foi possível exportar o Excel. Tente novamente.')
    } finally { pending.current = false; setBusy(false) }
  }

  return <section className="panel" aria-label="Exportar planilhas Excel">
    <div className="panel__body flex flex-wrap items-end gap-4">
      <div className="min-w-0 flex-1"><h2 className="font-bold">Exportar planilhas Excel</h2>
        <p className="mt-1 text-sm text-slate-500">Um pacote ZIP com quatro arquivos separados: pagamentos, clientes, serviços e projetos.</p>
        <p id="excel-period-help" className="mt-1 text-xs text-slate-500">{label}</p></div>
      <div><label htmlFor="excel-period" className="mb-1 block text-sm font-medium">Período da exportação</label>
        <select id="excel-period" value={period} disabled={busy} aria-describedby="excel-period-help" onChange={event => setPeriod(event.target.value)}>
          <option value="3">Últimos 3 meses</option><option value="6">Últimos 6 meses</option>
          <option value="12">Últimos 12 meses</option><option value="total">Total</option>
        </select></div>
      <Button loading={busy} onClick={() => void download()}>{busy ? 'Gerando planilhas…' : 'Baixar planilhas'}</Button>
      {import.meta.env.VITE_CLOUD_DEMO === 'true' && <p className="w-full text-sm text-slate-500">A demonstração permite até 2.000 registros por exportação. Se necessário, reduza o período.</p>}
      {busy && <p role="status" className="w-full text-sm text-slate-500">Preparando o arquivo. Aguarde a conclusão do download.</p>}
      {error && <div className="w-full"><Alert tone="error">{error}</Alert></div>}
    </div>
  </section>
}
