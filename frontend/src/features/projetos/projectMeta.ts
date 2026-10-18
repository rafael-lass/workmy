import type { ProjectStatus } from '../../types'

export const projectStatusLabel: Record<ProjectStatus, string> = { DISCOVERY: 'Planejamento', IN_PROGRESS: 'Andamento', REVIEW: 'Revisão', COMPLETED: 'Finalizado', ARCHIVED: 'Arquivado' }
export const projectTransitions: Record<ProjectStatus, ProjectStatus[]> = { DISCOVERY: ['IN_PROGRESS', 'ARCHIVED'], IN_PROGRESS: ['REVIEW', 'ARCHIVED'], REVIEW: ['IN_PROGRESS', 'COMPLETED', 'ARCHIVED'], COMPLETED: ['ARCHIVED'], ARCHIVED: ['DISCOVERY'] }
export const projectStatusTone = (status: ProjectStatus) => status === 'COMPLETED' ? 'success' as const : status === 'ARCHIVED' ? 'neutral' as const : status === 'REVIEW' ? 'warning' as const : 'info' as const
