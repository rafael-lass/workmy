import { useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { useApi } from '../../hooks/useApi'
import { IMAGE_ACCEPT, readImageDataUrl } from '../../lib/image'
import { Alert } from '../../shared/ui/Alert'
import { Button } from '../../shared/ui/Button'
import { Dialog } from '../../shared/ui/Dialog'
import { Field, fieldA11y } from '../../shared/ui/Field'
import { RichTextEditor } from '../../shared/ui/RichTextEditor'
import type { RichNode, Servico } from '../../types'
import { TagSelector } from './TagSelector'

type Props = { open: boolean; servico?: Servico | null; onClose: () => void; onSaved: (servico: Servico) => void }
const textLength = (node?: RichNode): number => (node?.text?.length ?? 0) + (node?.content?.reduce((sum, child) => sum + textLength(child), 0) ?? 0)

export function ServicoFormDialog(props: Props) { return props.open ? <ServiceForm key={props.servico?.id ?? 'new'} {...props} /> : null }

function ServiceForm({ servico, onClose, onSaved }: Props) {
  const { request } = useApi()
  const [nome, setNome] = useState(servico?.nome ?? '')
  const [document, setDocument] = useState(servico?.descricao_documento ?? null)
  const [tags, setTags] = useState(servico?.tags ?? [])
  const [image, setImage] = useState(servico?.imagem_base64 ?? '')
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [apiError, setApiError] = useState('')
  const [busy, setBusy] = useState(false)
  const [reading, setReading] = useState(false)
  const [tagBusy, setTagBusy] = useState(false)
  const lock = useRef(false)
  const pending = busy || reading || tagBusy
  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (lock.current || pending) return
    const next: Record<string, string> = {}
    if (!nome.trim()) next.nome = 'Informe o nome do serviço.'
    if (textLength(document?.doc) > 20000) next.descricao = 'Use no máximo 20.000 caracteres.'
    if (tags.length > 10) next.tags = 'Selecione no máximo 10 tags.'
    setErrors(next)
    if (Object.keys(next).length) return
    lock.current = true; setBusy(true); setApiError('')
    try {
      const saved = await request<Servico>(servico ? `/servicos/${servico.id}` : '/servicos/', { method: servico ? 'PUT' : 'POST', body: { nome: nome.trim(), descricao_documento: document, tag_ids: tags.map((tag) => tag.id), imagem_base64: image || null } })
      onSaved(saved); onClose()
    } catch (error) { setApiError(error instanceof Error ? error.message : 'Não foi possível salvar o serviço.') } finally { lock.current = false; setBusy(false) }
  }
  return <Dialog open title={servico ? 'Editar serviço' : 'Novo serviço'} description="Apresente seu trabalho com clareza. A descrição também será usada no PDF comercial." busy={pending} size="lg" onClose={onClose} footer={<><Button variant="secondary" onClick={onClose} disabled={pending}>Cancelar</Button><Button type="submit" form="servico-form" loading={busy} disabled={reading || tagBusy}>{servico ? 'Salvar alterações' : 'Criar serviço'}</Button></>}>
    <form id="servico-form" onSubmit={submit} noValidate><fieldset disabled={busy} className="min-w-0 space-y-5 border-0 p-0">
      {apiError && <Alert tone="error">{apiError}</Alert>}
      <Field id="servico-nome" label="Nome" error={errors.nome}><input id="servico-nome" data-autofocus maxLength={150} value={nome} onChange={(event) => setNome(event.target.value)} {...fieldA11y('servico-nome', errors.nome)} /></Field>
      <Field id="servico-imagem" label="Imagem de capa" optional hint="PNG, JPEG ou WebP de até 5 MiB."><input id="servico-imagem" type="file" disabled={reading} accept={IMAGE_ACCEPT} onChange={async (event) => { const file = event.target.files?.[0]; if (!file) return; setReading(true); try { setImage(await readImageDataUrl(file)); setApiError('') } catch (error) { setApiError(error instanceof Error ? error.message : 'Imagem inválida.') } finally { setReading(false) } }} /></Field>
      {image && <img src={image} alt="Prévia da capa" className="max-h-40 w-full rounded-xl object-contain" />}
      <div><p className="mb-2 text-sm font-semibold">Descrição formatada <span className="font-normal text-slate-500">(opcional)</span></p><RichTextEditor initialValue={servico?.descricao_documento} onChange={setDocument} disabled={busy} error={errors.descricao} /></div>
      <TagSelector selected={tags} onChange={setTags} disabled={busy} onBusyChange={setTagBusy} />{errors.tags && <p role="alert" className="text-red-700">{errors.tags}</p>}
    </fieldset></form>
  </Dialog>
}
