from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from src.domain.exceptions.business_exceptions import ValidaEntidadeException
from src.domain.time import business_today


VALID_PAYMENT_TYPES = {"MENSAL", "AVULSO"}
VALID_PAYMENT_STATUSES = {"PENDENTE", "PAGO", "CANCELADO", "ESTORNADO"}


@dataclass
class PagamentoEntity:
    projeto_id: int
    valor: Decimal
    data_vencimento: date
    id: int | None = None
    tipo_pagamento: str = "AVULSO"
    status: str = "PAGO"
    data_pagamento: date | None = None
    observacao: str | None = None
    referencia_mes: str | None = None
    gerado_automaticamente: bool = False
    comprovante_bytes: bytes | None = None
    comprovante_mime: str | None = None
    status_alterado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    motivo_ajuste: str | None = None
    criado_em: datetime | None = None
    atualizado_em: datetime | None = None

    def validate(self) -> None:
        if self.valor <= 0:
            raise ValidaEntidadeException("O valor do pagamento deve ser maior que zero.")
        if self.tipo_pagamento not in VALID_PAYMENT_TYPES:
            raise ValidaEntidadeException(f"Tipo de pagamento inválido: {self.tipo_pagamento}")
        if self.status not in VALID_PAYMENT_STATUSES:
            raise ValidaEntidadeException(f"Status financeiro inválido: {self.status}")

        if self.tipo_pagamento == "MENSAL":
            if self.referencia_mes is None:
                raise ValidaEntidadeException("Mensalidades devem possuir uma referência de mês.")
            if not self.gerado_automaticamente:
                raise ValidaEntidadeException("Mensalidades são criadas somente pela recorrência.")
        elif self.referencia_mes is not None:
            raise ValidaEntidadeException("Pagamentos avulsos não podem possuir referência mensal.")

        if self.gerado_automaticamente and self.tipo_pagamento != "MENSAL":
            raise ValidaEntidadeException("Somente mensalidades podem ser geradas automaticamente.")

        if self.referencia_mes is not None:
            parts = self.referencia_mes.split("-")
            if len(parts) != 2 or len(parts[0]) != 4 or len(parts[1]) != 2:
                raise ValidaEntidadeException("O formato de referência de mês deve ser YYYY-MM.")
            try:
                _, mes = int(parts[0]), int(parts[1])
            except ValueError as exc:
                raise ValidaEntidadeException("Os campos de referência devem ser numéricos.") from exc
            if not 1 <= mes <= 12:
                raise ValidaEntidadeException("Mês de referência inválido.")

        if self.status == "PENDENTE" and self.data_pagamento is not None:
            raise ValidaEntidadeException("Uma cobrança pendente não possui data de pagamento.")
        if self.status in {"PAGO", "ESTORNADO"}:
            if self.data_pagamento is None:
                raise ValidaEntidadeException("Um pagamento confirmado exige data de pagamento.")
            if self.data_pagamento > business_today():
                raise ValidaEntidadeException("A data do recebimento não pode estar no futuro.")
        if self.status in {"CANCELADO", "ESTORNADO"} and not (self.motivo_ajuste or "").strip():
            raise ValidaEntidadeException("Informe o motivo do cancelamento ou estorno.")

    def receber(
        self,
        data_pagamento: date,
        observacao: str | None = None,
        comprovante_bytes: bytes | None = None,
        comprovante_mime: str | None = None,
    ) -> None:
        if self.status != "PENDENTE":
            raise ValidaEntidadeException("Somente cobranças pendentes podem ser recebidas.")
        self.status = "PAGO"
        self.data_pagamento = data_pagamento
        if observacao is not None:
            self.observacao = observacao
        if comprovante_bytes is not None:
            self.comprovante_bytes = comprovante_bytes
            self.comprovante_mime = comprovante_mime
        self._touch_status()
        self.validate()

    def cancelar(self, motivo: str) -> None:
        if self.status != "PENDENTE":
            raise ValidaEntidadeException("Somente cobranças pendentes podem ser canceladas.")
        self.status = "CANCELADO"
        self.motivo_ajuste = motivo.strip()
        self._touch_status()
        self.validate()

    def estornar(self, motivo: str) -> None:
        if self.status != "PAGO":
            raise ValidaEntidadeException("Somente pagamentos confirmados podem ser estornados.")
        self.status = "ESTORNADO"
        self.motivo_ajuste = motivo.strip()
        self._touch_status()
        self.validate()

    def atualizar_detalhes(
        self,
        observacao: str | None,
        comprovante_bytes: bytes | None,
        comprovante_mime: str | None,
    ) -> None:
        self.observacao = observacao
        self.comprovante_bytes = comprovante_bytes
        self.comprovante_mime = comprovante_mime
        self.validate()

    def em_atraso(self, hoje: date | None = None) -> bool:
        return self.status == "PENDENTE" and self.data_vencimento < (hoje or business_today())

    def _touch_status(self) -> None:
        self.status_alterado_em = datetime.now(timezone.utc).replace(tzinfo=None)
