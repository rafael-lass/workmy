import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useApi } from '../../hooks/useApi'
import { useAuth } from '../../hooks/useAuth'
import { Dialog } from '../../shared/ui/Dialog'
import { Button } from '../../shared/ui/Button'
import { Field, fieldA11y } from '../../shared/ui/Field'
import { Alert } from '../../shared/ui/Alert'
import { RichTextEditor } from '../../shared/ui/RichTextEditor'
import { Badge } from '../../shared/ui/Badge'
import type { Servico } from '../../types'

export function ServiceViewDialog({ service, onClose }: { service: Servico; onClose: () => void }) {
  return <Dialog open title={service.nome} size="lg" onClose={onClose} footer={<Button variant="secondary" onClick={onClose}>Fechar</Button>}>
    {service.imagem_base64 && <img className="mb-5 max-h-72 w-full rounded-xl object-contain" src={service.imagem_base64} alt={`Capa de ${service.nome}`} />}
    <div className="mb-4 flex flex-wrap gap-2">{service.tags.map((tag) => <Badge key={tag.id} tone="info">{tag.nome}</Badge>)}</div>
    {service.descricao_documento ? <RichTextEditor initialValue={service.descricao_documento} readOnly /> : <p className="text-slate-500">Sem descrição cadastrada.</p>}
  </Dialog>
}

export function ServicePdfDialog({ service, onClose }: { service: Servico; onClose: () => void }) {
  const { user } = useAuth()
  const { request } = useApi()
  const [name, setName] = useState(user?.username ?? '')
  const [email, setEmail] = useState(user?.email ?? '')
  const [phone, setPhone] = useState(user?.telefone ?? '')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const lock = useRef(false)
  const submit = async (event: FormEvent) => {
    event.preventDefault(); if (lock.current) return
    const next: Record<string, string> = {}
    if (!name.trim()) next.name = 'Informe seu nome profissional.'
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) next.email = 'Informe um e-mail válido.'
    if (phone && !/^(?:55)?\d{10,11}$/.test(phone.replace(/\D/g, ''))) next.phone = 'Informe DDD e telefone válido.'
    setErrors(next); if (Object.keys(next).length) return
    lock.current = true; setBusy(true); setError('')
    try {
      const blob = await request<Blob>(`/servicos/${service.id}/pdf`, { method: 'POST', responseType: 'blob', body: { nome_profissional: name.trim(), email: email.trim(), telefone: phone || null } })
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `${service.nome.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 80) || 'servico'}.pdf`; document.body.append(anchor); anchor.click(); anchor.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 1000)
      onClose()
    } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível exportar o PDF.') } finally { lock.current = false; setBusy(false) }
  }
  return <Dialog open title="Exportar apresentação em PDF" description="Revise seus contatos. Estas alterações valem somente para este PDF e não alteram sua conta." busy={busy} onClose={onClose} footer={<><Button variant="secondary" disabled={busy} onClick={onClose}>Cancelar</Button><Button type="submit" form="service-pdf" loading={busy}>Baixar PDF</Button></>}><form id="service-pdf" onSubmit={submit} noValidate><fieldset disabled={busy} className="space-y-4 border-0 p-0">{error && <Alert tone="error">{error}</Alert>}<Field id="pdf-name" label="Nome profissional" error={errors.name}><input id="pdf-name" data-autofocus value={name} maxLength={100} onChange={(event) => setName(event.target.value)} {...fieldA11y('pdf-name', errors.name)} /></Field><Field id="pdf-email" label="E-mail" error={errors.email}><input id="pdf-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} {...fieldA11y('pdf-email', errors.email)} /></Field><Field id="pdf-phone" label="Telefone" optional error={errors.phone}><input id="pdf-phone" type="tel" value={phone} maxLength={20} onChange={(event) => setPhone(event.target.value)} {...fieldA11y('pdf-phone', errors.phone)} /></Field><p className="text-sm text-slate-500">A apresentação inclui o serviço salvo, sua capa, descrição e tags. Não inclui preços, clientes ou dados financeiros.</p></fieldset></form></Dialog>
}
