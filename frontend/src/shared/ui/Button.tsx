import type { ButtonHTMLAttributes, ReactNode } from 'react'

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' | 'ghost'; size?: 'sm' | 'md'; loading?: boolean; children: ReactNode }

export function Button({ variant = 'primary', size = 'md', loading = false, disabled, className = '', children, ...props }: Props) {
  return <button className={`ui-button ui-button--${variant} ui-button--${size} ${className}`} disabled={disabled || loading} aria-busy={loading} {...props}>{loading && <span className="ui-button__spinner" aria-hidden="true" />}{children}</button>
}
