/* eslint-disable react-refresh/only-export-components */
import type { ReactNode } from 'react'

export function Field({ id, label, error, optional, hint, children }: { id: string; label: string; error?: string; optional?: boolean; hint?: string; children: ReactNode }) {
  return <div className="ui-field"><label htmlFor={id}>{label} {optional && <span>(opcional)</span>}</label><div>{children}</div>{error ? <p id={`${id}-error`} className="ui-field__error" role="alert">{error}</p> : hint ? <p id={`${id}-hint`} className="ui-field__hint">{hint}</p> : null}</div>
}

export const fieldA11y = (id: string, error?: string, hint?: string) => ({ 'aria-invalid': error ? true : undefined, 'aria-describedby': error ? `${id}-error` : hint ? `${id}-hint` : undefined })
