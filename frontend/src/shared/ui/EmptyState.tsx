import type { ReactNode } from 'react'
import { Icon } from './Icon'

type EmptyStateProps = {
  title: string
  description?: string
  action?: ReactNode
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return <div className="ui-empty"><span><Icon name="projects" /></span><h3>{title}</h3>{description && <p>{description}</p>}{action}</div>
}
