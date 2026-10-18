import { NavLink, Outlet } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Icon } from '../shared/ui/Icon'

const nav = [
  { to: '/dashboard', label: 'Dashboard', icon: 'dashboard' as const },
  { to: '/projetos', label: 'Projetos', icon: 'projects' as const },
  { to: '/clientes', label: 'Clientes', icon: 'clients' as const },
  { to: '/servicos', label: 'Serviços', icon: 'services' as const },
  { to: '/financeiro', label: 'Financeiro', icon: 'finance' as const },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const initials = user?.username.slice(0, 2).toUpperCase() ?? 'WM'

  return <div className="min-h-screen bg-[#f5f7fb]">
    {open && <button className="fixed inset-0 z-40 bg-slate-950/45 lg:hidden" aria-label="Fechar menu" onClick={() => setOpen(false)} />}
    <aside className={`fixed inset-y-0 left-0 z-50 flex w-[252px] flex-col border-r border-white/10 bg-[#11182a] text-white transition-transform lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
      <div className="flex h-[76px] items-center justify-between border-b border-white/10 px-6">
        <div className="flex items-center gap-3"><span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-500 font-black">W</span><div><strong className="block text-lg leading-none">WorkMy</strong><span className="text-[11px] text-white/45">gestão sem ruído</span></div></div>
        <button className="ui-icon-button text-white lg:hidden" onClick={() => setOpen(false)} aria-label="Fechar menu"><Icon name="close" /></button>
      </div>
      <nav className="flex-1 space-y-1 px-3 py-6" aria-label="Navegação principal">
        {nav.map((item) => <NavLink key={item.to} to={item.to} onClick={() => setOpen(false)} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold transition ${isActive ? 'bg-white text-[#172033] shadow-lg' : 'text-white/65 hover:bg-white/8 hover:text-white'}`}><Icon name={item.icon} className="h-5 w-5" />{item.label}</NavLink>)}
      </nav>
      <div className="border-t border-white/10 p-3">
        <button onClick={() => void logout()} className="flex w-full items-center gap-3 rounded-xl px-4 py-3 text-sm font-semibold text-white/60 hover:bg-white/8 hover:text-white"><Icon name="logout" className="h-5 w-5" />Sair</button>
      </div>
    </aside>
    <header className="fixed inset-x-0 top-0 z-30 flex h-[68px] items-center justify-between border-b border-slate-200/80 bg-white/90 px-4 backdrop-blur-lg lg:left-[252px] lg:px-8">
      <button className="ui-icon-button lg:hidden" onClick={() => setOpen(true)} aria-label="Abrir menu"><Icon name="menu" /></button>
      <div className="hidden lg:block"><span className="text-xs font-semibold uppercase tracking-[.12em] text-slate-400">Área de trabalho</span></div>
      <div className="flex items-center gap-3">
        <div className="hidden text-right sm:block"><strong className="block text-sm leading-tight">{user?.username}</strong><span className="block max-w-44 truncate text-xs text-slate-500">{user?.email}</span></div>
        <span className="grid h-9 w-9 place-items-center rounded-xl bg-indigo-50 text-xs font-black text-indigo-700">{initials}</span>
      </div>
    </header>
    <main className="min-h-screen px-4 pb-10 pt-[92px] sm:px-6 lg:ml-[252px] lg:px-8"><Outlet /></main>
  </div>
}
