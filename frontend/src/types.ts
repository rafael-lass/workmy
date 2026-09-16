export type User = {
  id: number
  username: string
  email: string
  telefone?: string | null
}

export type Cliente = {
  id: number
  nome: string
  empresa: string
  email?: string | null
  telefone?: string | null
  total_acumulado: string
  criado_em: string
}

export type ServiceTag = { id: number; nome: string }
export type RichNode = { type: string; text?: string; attrs?: Record<string, unknown>; marks?: { type: string; attrs?: Record<string, unknown> }[]; content?: RichNode[] }
export type ServiceDocument = { version: 1; doc: RichNode }
export type Servico = {
  id: number
  nome: string
  descricao_documento?: ServiceDocument | null
  descricao_resumo?: string
  tags: ServiceTag[]
  imagem_base64?: string | null
  criado_em: string
}

export type ProjectStatus =
  | 'DISCOVERY'
  | 'IN_PROGRESS'
  | 'REVIEW'
  | 'COMPLETED'
  | 'ARCHIVED'

export type Projeto = {
  id: number
  cliente_id: number
  cliente_nome: string
  servico_id: number
  servico_nome: string
  valor_mensal: string | null
  dia_vencimento: number
  recorrencia_inicio: string | null
  criado_em: string
  status: ProjectStatus
  progresso: number
  tipo_recorrencia: 'MENSAL' | 'AVULSO'
  valor: string | null
  ativo: boolean
  total_acumulado: string
  possui_lancamentos: boolean
}

export type PaymentStatus = 'PENDENTE' | 'PAGO' | 'CANCELADO' | 'ESTORNADO'

export type Pagamento = {
  id: number
  projeto_id: number
  cliente_id: number
  projeto_cliente_nome: string
  projeto_servico_nome: string
  valor: string
  tipo_pagamento: 'MENSAL' | 'AVULSO'
  tipo_pagamento_display: string
  status: PaymentStatus
  em_atraso: boolean
  data_vencimento: string
  data_pagamento?: string | null
  referencia_mes?: string | null
  gerado_automaticamente: boolean
  observacao?: string | null
  comprovante_base64?: string | null
  motivo_ajuste?: string | null
  status_alterado_em: string
  criado_em: string
  atualizado_em: string
}

export type PagamentoList = {
  items: Pagamento[]
  total: number
  page: number
  page_size: number
}

export type DashboardResumo = {
  recebido_mes: string
  pendente_total: string
  atrasado_total: string
  previsto_proximo_mes: string
  projetos_ativos: number
  clientes_total: number
  serie_seis_meses: Array<{ mes: string; total: string }>
  ultimos_recebimentos: Pagamento[]
}

export type BillingResult = {
  pagamentos_gerados: number
  valor_total: string
  referencias: string[]
  detalhes: Array<{
    pagamento_id: number
    projeto_id: number
    valor: string
    referencia_mes: string
    data_vencimento: string
    status: PaymentStatus
  }>
}
