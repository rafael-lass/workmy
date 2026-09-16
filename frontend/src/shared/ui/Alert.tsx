import type { ReactNode } from 'react'
export function Alert({ tone = 'info', children }: { tone?: 'info' | 'error' | 'warning' | 'success'; children: ReactNode }) { return <div className={`ui-alert ui-alert--${tone}`} role={tone === 'error' ? 'alert' : 'status'}>{children}</div> }
