import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useApi } from '../../hooks/useApi'
import { ApiError } from '../../lib/http'
import { isMaskedBrazilianPhoneValid, maskBrazilianPhone } from '../../lib/phone'
import { Alert } from '../../shared/ui/Alert'
import { Button } from '../../shared/ui/Button'
import { Dialog } from '../../shared/ui/Dialog'
import { Field, fieldA11y } from '../../shared/ui/Field'
import type { Cliente } from '../../types'

type Form = { nome: string; empresa: string; email: string; telefone: string }
const emptyForm: Form = { nome: '', empresa: '', email: '', telefone: '' }

export function ClienteFormDialog({ open, cliente, onClose, onSaved }: { open: boolean; cliente?: Cliente | null; onClose: () => void; onSaved: (cliente: Cliente) => void }) {
  const { request } = useApi()
  const [form, setForm] = useState<Form>(emptyForm)
  const [errors, setErrors] = useState<Partial<Record<keyof Form, string>>>({})
  const [apiError, setApiError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (!open) return
    setForm(cliente ? { nome: cliente.nome, empresa: cliente.empresa === 'Não informada' ? '' : cliente.empresa, email: cliente.email ?? '', telefone: cliente.telefone ?? '' } : emptyForm)
    setErrors({}); setApiError(''); setBusy(false)
  }, [open, cliente])

  const update = (key: keyof Form, value: string) => { setForm((current) => ({ ...current, [key]: value })); setErrors((current) => ({ ...current, [key]: undefined })) }
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    const nextErrors: typeof errors = {}
    if (!form.nome.trim()) nextErrors.nome = 'Informe o nome do cliente.'
    if (form.email && !/^\S+@\S+\.\S+$/.test(form.email)) nextErrors.email = 'Informe um e-mail válido.'
    if (!isMaskedBrazilianPhoneValid(form.telefone)) nextErrors.telefone = 'Use um telefone brasileiro com DDD.'
    if (Object.keys(nextErrors).length) { setErrors(nextErrors); return }
    setBusy(true); setApiError('')
    try {
      const saved = await request<Cliente>(cliente ? `/clientes/${cliente.id}` : '/clientes/', { method: cliente ? 'PUT' : 'POST', body: { nome: form.nome.trim(), empresa: form.empresa.trim() || 'Não informada', email: form.email.trim() || null, telefone: form.telefone || null } })
      onSaved(saved); onClose()
    } catch (error) { setApiError(error instanceof ApiError ? error.message : 'Não foi possível salvar o cliente.') } finally { setBusy(false) }
  }

  return <Dialog open={open} title={cliente ? 'Editar cliente' : 'Novo cliente'} description="Mantenha os dados de contato em um único cadastro." busy={busy} onClose={onClose} footer={<><Button variant="secondary" onClick={onClose} disabled={busy}>Cancelar</Button><Button type="submit" form="cliente-form" loading={busy}>{cliente ? 'Salvar alterações' : 'Criar cliente'}</Button></>}>
    <form id="cliente-form" className="form-grid" onSubmit={submit} noValidate>
      {apiError && <div className="form-span-2"><Alert tone="error">{apiError}</Alert></div>}
      <Field id="cliente-nome" label="Nome" error={errors.nome}><input id="cliente-nome" data-autofocus value={form.nome} onChange={(event) => update('nome', event.target.value)} maxLength={100} {...fieldA11y('cliente-nome', errors.nome)} /></Field>
      <Field id="cliente-empresa" label="Empresa" optional><input id="cliente-empresa" value={form.empresa} onChange={(event) => update('empresa', event.target.value)} maxLength={100} /></Field>
      <Field id="cliente-email" label="E-mail" optional error={errors.email}><input id="cliente-email" type="email" value={form.email} onChange={(event) => update('email', event.target.value)} autoComplete="email" {...fieldA11y('cliente-email', errors.email)} /></Field>
      <Field id="cliente-telefone" label="Telefone" optional error={errors.telefone}><input id="cliente-telefone" type="tel" value={form.telefone} onChange={(event) => update('telefone', maskBrazilianPhone(event.target.value))} placeholder="(11) 99999-9999" autoComplete="tel" {...fieldA11y('cliente-telefone', errors.telefone)} /></Field>
    </form>
  </Dialog>
}
