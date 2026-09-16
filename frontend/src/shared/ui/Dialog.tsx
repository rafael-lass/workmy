import { useEffect, useId, useRef } from 'react'
import type { ReactNode } from 'react'
import { Icon } from './Icon'

const focusable = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

export function Dialog({ open, title, description, busy = false, size = 'md', onClose, children, footer }: { open: boolean; title: string; description?: string; busy?: boolean; size?: 'sm' | 'md' | 'lg'; onClose: () => void; children: ReactNode; footer?: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null)
  const triggerRef = useRef<HTMLElement | null>(null)
  const titleId = useId()
  const descriptionId = useId()
  useEffect(() => { const dialog = ref.current; if (!dialog) return; if (open && !dialog.open) { triggerRef.current = document.activeElement as HTMLElement | null; dialog.showModal(); const initialFocus = dialog.querySelector<HTMLElement>('[data-autofocus]') ?? dialog.querySelector<HTMLElement>('input, select, textarea, button'); initialFocus?.focus() } else if (!open && dialog.open) dialog.close() }, [open])
  useEffect(() => () => triggerRef.current?.focus(), [])
  const requestClose = () => { if (!busy) onClose() }
  return <dialog ref={ref} className={`ui-dialog ui-dialog--${size}`} aria-labelledby={titleId} aria-describedby={description ? descriptionId : undefined} aria-busy={busy} onCancel={(event) => { event.preventDefault(); requestClose() }} onClick={(event) => { if (event.target === ref.current) requestClose() }} onKeyDown={(event) => { if (event.key !== 'Tab') return; const elements = Array.from(ref.current?.querySelectorAll<HTMLElement>(focusable) ?? []); if (!elements.length) return; const first = elements[0]; const last = elements[elements.length - 1]; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() } }}><section className="ui-dialog__panel"><header className="ui-dialog__header"><div><h2 id={titleId}>{title}</h2>{description && <p id={descriptionId}>{description}</p>}</div><button type="button" className="ui-icon-button" onClick={requestClose} disabled={busy} aria-label="Fechar diálogo"><Icon name="close" /></button></header><div className="ui-dialog__body">{children}</div>{footer && <footer className="ui-dialog__footer">{footer}</footer>}</section></dialog>
}
