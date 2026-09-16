import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { ServicoFormDialog } from '../features/servicos/ServicoFormDialog'
import { ServicePdfDialog, ServiceViewDialog } from '../features/servicos/ServicePresentationDialogs'
import { useApi } from '../hooks/useApi'
import { Alert } from '../shared/ui/Alert'
import { Badge } from '../shared/ui/Badge'
import { Button } from '../shared/ui/Button'
import { ConfirmDialog } from '../shared/ui/ConfirmDialog'
import { EmptyState } from '../shared/ui/EmptyState'
import { Icon } from '../shared/ui/Icon'
import { PageHeader } from '../shared/ui/PageHeader'
import { PageSkeleton } from '../shared/ui/Skeleton'
import { useToast } from '../shared/ui/Toast'
import type { Servico } from '../types'

export function ServicosPage() {
  const { request } = useApi()
  const { notify } = useToast()
  const [params, setParams] = useSearchParams()
  const [items, setItems] = useState<Servico[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [search, setSearch] = useState('')
  const [editing, setEditing] = useState<Servico | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [deleting, setDeleting] = useState<Servico | null>(null)
  const [viewing, setViewing] = useState<Servico | null>(null)
  const [exporting, setExporting] = useState<Servico | null>(null)
  const [deleteBusy, setDeleteBusy] = useState(false)
  const load = useCallback(async () => { setLoading(true); setError(''); try { setItems(await request<Servico[]>('/servicos/')) } catch (err) { setError(err instanceof Error ? err.message : 'Não foi possível carregar os serviços.') } finally { setLoading(false) } }, [request])
  useEffect(() => { void load() }, [load])
  useEffect(() => { if (params.get('acao') === 'novo') { setEditing(null); setFormOpen(true) } }, [params])
  const closeForm = () => { setFormOpen(false); setEditing(null); if (params.has('acao')) { const next = new URLSearchParams(params); next.delete('acao'); setParams(next, { replace: true }) } }
  const filtered = useMemo(() => { const term = search.trim().toLocaleLowerCase(); return items.filter((item) => !term || [item.nome, item.descricao_resumo, ...item.tags.map((tag) => tag.nome)].some((value) => value?.toLocaleLowerCase().includes(term))) }, [items, search])
  const remove = async () => { if (!deleting || deleteBusy) return; setDeleteBusy(true); try { await request(`/servicos/${deleting.id}`, { method: 'DELETE' }); setItems((current) => current.filter((item) => item.id !== deleting.id)); setDeleting(null); notify('Serviço excluído.') } catch (err) { notify(err instanceof Error ? err.message : 'Não foi possível excluir o serviço.', 'error') } finally { setDeleteBusy(false) } }
  if (loading) return <PageSkeleton />
  return <div className="page-shell">
    <PageHeader eyebrow="Seu catálogo" title="Serviços" description="Organize suas entregas e compartilhe uma apresentação profissional com seus clientes." actions={<Button onClick={() => { setEditing(null); setFormOpen(true) }}><Icon name="plus" />Novo serviço</Button>} />
    {error && <Alert tone="error">{error}<Button variant="secondary" onClick={() => void load()}>Tentar novamente</Button></Alert>}
    <div className="toolbar !grid-cols-1"><div className="search-field"><Icon name="search" /><input aria-label="Buscar serviços" placeholder="Buscar por nome, descrição ou tag" value={search} onChange={(event) => setSearch(event.target.value)} /></div></div>
    {filtered.length ? <section className="grid gap-5 sm:grid-cols-2 xl:grid-cols-3">{filtered.map((service) => <article key={service.id} className="panel flex flex-col overflow-hidden">
      <div className="relative h-36 bg-gradient-to-br from-indigo-100 to-emerald-50">{service.imagem_base64 ? <img src={service.imagem_base64} alt="" className="h-full w-full object-cover" /> : <div className="grid h-full place-items-center text-4xl font-black text-indigo-300">{service.nome.charAt(0).toUpperCase()}</div>}<div className="absolute right-3 top-3 flex gap-1 rounded-xl bg-white/90 p-1 shadow"><button className="ui-icon-button !h-8 !w-8" aria-label={`Editar ${service.nome}`} onClick={() => { setEditing(service); setFormOpen(true) }}><Icon name="edit" /></button><button className="ui-icon-button !h-8 !w-8 text-red-600" aria-label={`Excluir ${service.nome}`} onClick={() => setDeleting(service)}><Icon name="trash" /></button></div></div>
      <div className="flex flex-1 flex-col p-5"><h2 className="m-0 break-words text-lg font-bold tracking-tight">{service.nome}</h2><p className="mb-4 mt-2 line-clamp-3 min-h-[60px] text-sm leading-5 text-slate-600">{service.descricao_resumo || 'Sem descrição cadastrada.'}</p><div className="mb-5 flex flex-wrap gap-2">{service.tags.map((tag) => <Badge key={tag.id} tone="info">{tag.nome}</Badge>)}</div><div className="mt-auto flex flex-wrap gap-2 border-t border-slate-100 pt-4"><Button variant="secondary" size="sm" onClick={() => setViewing(service)}>Visualizar</Button><Button size="sm" onClick={() => setExporting(service)}>Exportar PDF</Button></div></div>
    </article>)}</section> : <section className="panel p-5"><EmptyState title={items.length ? 'Nenhum serviço encontrado' : 'Monte seu catálogo de serviços'} description={items.length ? 'Tente buscar por outro termo.' : 'Crie um serviço para reutilizar em projetos e compartilhar com clientes.'} action={!items.length ? <Button onClick={() => setFormOpen(true)}>Novo serviço</Button> : undefined} /></section>}
    <ServicoFormDialog open={formOpen} servico={editing} onClose={closeForm} onSaved={(saved) => { setItems((current) => editing ? current.map((item) => item.id === saved.id ? saved : item) : [saved, ...current]); notify(editing ? 'Serviço atualizado.' : 'Serviço criado.') }} />
    {viewing && <ServiceViewDialog service={viewing} onClose={() => setViewing(null)} />}
    {exporting && <ServicePdfDialog service={exporting} onClose={() => setExporting(null)} />}
    <ConfirmDialog open={Boolean(deleting)} title="Excluir serviço?" description={deleting ? `${deleting.nome} será removido. Serviços vinculados a projetos não podem ser excluídos.` : ''} confirmLabel="Excluir serviço" danger busy={deleteBusy} onConfirm={() => void remove()} onClose={() => setDeleting(null)} />
  </div>
}
