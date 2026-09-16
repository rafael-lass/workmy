import { Badge } from '../../shared/ui/Badge'
import type { Pagamento } from '../../types'

export function PaymentStatusBadge({ payment }: { payment: Pagamento }) {
  if (payment.em_atraso) return <Badge tone="danger">Atrasado</Badge>
  const data = payment.status === 'PAGO' ? ['success', 'Pago'] : payment.status === 'PENDENTE' ? ['warning', 'Pendente'] : payment.status === 'CANCELADO' ? ['neutral', 'Cancelado'] : ['danger', 'Estornado']
  return <Badge tone={data[0] as 'success' | 'warning' | 'neutral' | 'danger'}>{data[1]}</Badge>
}
