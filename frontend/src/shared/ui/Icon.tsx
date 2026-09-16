import type { ReactNode, SVGProps } from 'react'

export type IconName = 'dashboard' | 'projects' | 'clients' | 'services' | 'finance' | 'plus' | 'menu' | 'close' | 'logout' | 'search' | 'edit' | 'trash' | 'eye' | 'check' | 'pause' | 'play' | 'calendar' | 'arrow-right' | 'receipt' | 'refresh' | 'more'

const paths: Record<IconName, ReactNode> = {
  dashboard: <><rect x="3" y="3" width="7" height="7" rx="2"/><rect x="14" y="3" width="7" height="4" rx="2"/><rect x="14" y="11" width="7" height="10" rx="2"/><rect x="3" y="14" width="7" height="7" rx="2"/></>,
  projects: <><path d="M6 3v12"/><path d="M18 9v12"/><path d="M6 8h7a5 5 0 0 1 5 5"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="6" r="3"/></>,
  clients: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></>,
  services: <><rect x="3" y="3" width="18" height="18" rx="3"/><path d="M8 8h8M8 12h8M8 16h5"/></>,
  finance: <><rect x="3" y="5" width="18" height="14" rx="3"/><path d="M3 10h18M7 15h3"/></>,
  plus: <path d="M12 5v14M5 12h14"/>, menu: <path d="M4 6h16M4 12h16M4 18h16"/>, close: <path d="m6 6 12 12M18 6 6 18"/>,
  logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>, edit: <><path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/></>,
  trash: <><path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6M10 11v5M14 11v5"/></>, eye: <><path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/></>,
  check: <path d="m5 12 4 4L19 6"/>, pause: <path d="M9 5v14M15 5v14"/>, play: <path d="m8 5 11 7-11 7Z"/>,
  calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M16 3v4M8 3v4M3 10h18"/></>, 'arrow-right': <path d="M5 12h14m-6-6 6 6-6 6"/>,
  receipt: <><path d="M6 3h12v18l-3-2-3 2-3-2-3 2Z"/><path d="M9 8h6M9 12h6M9 16h3"/></>, refresh: <><path d="M20 7h-5V2"/><path d="M20 7a9 9 0 1 0 2 7"/></>,
  more: <><circle cx="5" cy="12" r="1" fill="currentColor"/><circle cx="12" cy="12" r="1" fill="currentColor"/><circle cx="19" cy="12" r="1" fill="currentColor"/></>,
}

export function Icon({ name, ...props }: { name: IconName } & SVGProps<SVGSVGElement>) {
  return <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}>{paths[name]}</svg>
}
