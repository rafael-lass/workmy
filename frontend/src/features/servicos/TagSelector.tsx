import { useEffect, useRef, useState } from 'react'
import { useApi } from '../../hooks/useApi'
import type { ServiceTag } from '../../types'

export function TagSelector({ selected, onChange, disabled, onBusyChange }: { selected: ServiceTag[]; onChange: (tags: ServiceTag[]) => void; disabled: boolean; onBusyChange: (busy: boolean) => void }) {
  const { request } = useApi()
  const [catalog, setCatalog] = useState<ServiceTag[]>([])
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const lock = useRef(false)
  useEffect(() => { let active = true; request<ServiceTag[]>('/servicos/tags').then((tags) => { if (active) setCatalog(tags) }).catch(() => { if (active) setError('Não foi possível carregar as tags. Reabra o formulário para tentar novamente.') }).finally(() => { if (active) setLoading(false) }); return () => { active = false } }, [request])
  const name = query.trim().replace(/\s+/g, ' ')
  const exact = [...catalog, ...selected].find((tag) => tag.nome.toLocaleLowerCase() === name.toLocaleLowerCase())
  const choices = catalog.filter((tag) => !selected.some((value) => value.id === tag.id) && tag.nome.toLocaleLowerCase().includes(name.toLocaleLowerCase()))
  const add = (tag: ServiceTag) => { if (selected.length < 10 && !selected.some((value) => value.id === tag.id)) onChange([...selected, tag]); setQuery('') }
  const create = async () => {
    if (!name || disabled || lock.current || selected.length >= 10) return
    if (exact) { add(exact); return }
    lock.current = true; setCreating(true); onBusyChange(true); setError('')
    try { const tag = await request<ServiceTag>('/servicos/tags', { method: 'POST', body: { nome: name } }); setCatalog((current) => [...current.filter((item) => item.id !== tag.id), tag]); add(tag) } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível criar a tag.') } finally { lock.current = false; setCreating(false); onBusyChange(false) }
  }
  return <div className="tag-selector"><label id="tags-label" htmlFor="service-tags">Tags <span className="text-slate-500">(opcional)</span></label><div className="tag-selector__selected">{selected.map((tag) => <button key={tag.id} type="button" disabled={disabled || creating} aria-label={`Remover tag ${tag.nome}`} onClick={() => onChange(selected.filter((item) => item.id !== tag.id))}>{tag.nome} ×</button>)}</div><input id="service-tags" value={query} maxLength={40} disabled={disabled || creating || selected.length >= 10} placeholder="Pesquisar ou criar uma tag" onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { event.preventDefault(); void create() } }} aria-describedby="tags-hint" /><p id="tags-hint" className="text-xs text-slate-500">{selected.length}/10 tags. Selecione abaixo ou digite um nome e pressione Enter.</p><div className="tag-selector__options">{choices.map((tag) => <button key={tag.id} type="button" disabled={disabled || creating || selected.length >= 10} onClick={() => add(tag)}>{tag.nome}</button>)}{name && !exact && <button type="button" disabled={disabled || creating || selected.length >= 10} onClick={() => void create()}>{creating ? 'Criando…' : `Criar “${name}”`}</button>}</div>{loading && <p role="status">Carregando tags…</p>}{error && <p role="alert" className="text-red-700">{error}</p>}</div>
}
