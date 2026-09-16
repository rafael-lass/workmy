/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

type Toast = { id: number; message: string; tone: 'success' | 'error' | 'info' }
const ToastContext = createContext<{ notify: (message: string, tone?: Toast['tone']) => void } | null>(null)
export function ToastProvider({ children }: { children: ReactNode }) { const [toasts, setToasts] = useState<Toast[]>([]); const notify = useCallback((message: string, tone: Toast['tone'] = 'success') => { const id = Date.now() + Math.random(); setToasts((current) => [...current, { id, message, tone }]); window.setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== id)), 4500) }, []); const value = useMemo(() => ({ notify }), [notify]); return <ToastContext.Provider value={value}>{children}<div className="ui-toast-region" aria-live="polite" aria-atomic="true">{toasts.map((toast) => <div key={toast.id} className={`ui-toast ui-toast--${toast.tone}`}>{toast.message}</div>)}</div></ToastContext.Provider> }
export function useToast() { const context = useContext(ToastContext); if (!context) throw new Error('useToast deve ser usado dentro de ToastProvider'); return context }
