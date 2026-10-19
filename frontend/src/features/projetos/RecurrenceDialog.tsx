import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useApi } from '../../hooks/useApi'
import { ApiError } from '../../lib/http'
import { Alert } from '../../shared/ui/Alert'
import { Button } from '../../shared/ui/Button'
import { Dialog } from '../../shared/ui/Dialog'
import { Field } from '../../shared/ui/Field'
import type { Projeto } from '../../types'
import { todayInput } from '../../lib/format'

export function RecurrenceDialog({ projeto, onClose, onSaved }: { projeto: Projeto | null; onClose: () => void; onSaved: (projeto: Projeto) => void }) {
  const submitting = useRef(false); const { request } = useApi(); const [value, setValue] = useState(''); const [day, setDay] = useState('5'); const [start, setStart] = useState(todayInput()); const [error, setError] = useState(''); const [busy, setBusy] = useState(false)
  useEffect(() => { if (!projeto) return; setValue(projeto.valor_mensal ?? ''); setDay(String(projeto.dia_vencimento)); setStart(todayInput()); setError(''); setBusy(false) }, [projeto])
  if (!projeto) return null
  const resuming = !projeto.ativo
  const enabling = projeto.tipo_recorrencia === 'AVULSO'
  const submit = async (event: FormEvent) => { event.preventDefault(); if (submitting.current) return; if (resuming && (!Number.isFinite(Number(value)) || Number(value) <= 0 || !Number.isInteger(Number(day)) || Number(day) < 1 || Number(day) > 28 || !start)) { setError('Informe valor mensal positivo, vencimento de 1 a 28 e a data inicial.'); return } submitting.current = true; setBusy(true); setError(''); try { await request(`/projetos/${projeto.id}/recorrencia`, { method: 'PATCH', body: resuming ? { ativo: true, valor_mensal: Number(value), dia_vencimento: Number(day), recorrencia_inicio: start } : { ativo: false } }); const refreshed = await request<Projeto>(`/projetos/${projeto.id}`); onSaved(refreshed); onClose() } catch (err) { setError(err instanceof ApiError ? err.message : 'Não foi possível alterar a recorrência.') } finally { submitting.current = false; setBusy(false) } }
  return <Dialog open title={enabling ? 'Ativar cobrança mensal' : resuming ? 'Retomar recorrência' : 'Pausar recorrência'} description={enabling ? 'Defina valor, vencimento e início. As mensalidades já vencidas serão criadas como pendentes.' : resuming ? 'Escolha a nova data inicial. Cobranças vencidas desde essa data serão geradas sem duplicação.' : 'Desativa novas mensalidades. O histórico e as pendências já geradas serão preservados.'} busy={busy} size="sm" onClose={onClose} footer={<><Button variant="secondary" disabled={busy} onClick={onClose}>Voltar</Button><Button type="submit" form="recurrence-form" loading={busy}>{enabling ? 'Ativar mensal' : resuming ? 'Retomar' : 'Pausar'}</Button></>}><form id="recurrence-form" className="grid gap-4" onSubmit={submit}>{error && <Alert tone="error">{error}</Alert>}{resuming ? <><Field id="recurrence-value" label="Novo valor mensal"><input id="recurrence-value" data-autofocus type="number" min="0.01" step="0.01" value={value} onChange={(event) => setValue(event.target.value)} /></Field><Field id="recurrence-day" label="Dia do vencimento"><input id="recurrence-day" type="number" min="1" max="28" value={day} onChange={(event) => setDay(event.target.value)} /></Field><Field id="recurrence-start" label={enabling ? "Início da cobrança mensal" : "Nova data inicial"}><input id="recurrence-start" type="date" min={enabling ? undefined : todayInput()} value={start} onChange={(event) => setStart(event.target.value)} /></Field></> : <Alert tone="warning">As cobranças pendentes continuam exigindo recebimento ou cancelamento manual.</Alert>}</form></Dialog>
}
