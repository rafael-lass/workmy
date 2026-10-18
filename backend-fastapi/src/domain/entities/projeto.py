from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from src.domain.exceptions.business_exceptions import ValidaEntidadeException

VALID_STATUSES = {"DISCOVERY", "IN_PROGRESS", "REVIEW", "COMPLETED", "ARCHIVED"}
VALID_RECURRENCE_TYPES = {"AVULSO", "MENSAL"}
STATUS_TRANSITIONS = {
    "DISCOVERY":    {"IN_PROGRESS", "ARCHIVED"},
    "IN_PROGRESS":  {"REVIEW", "ARCHIVED"},
    "REVIEW":       {"IN_PROGRESS", "COMPLETED", "ARCHIVED"},
    "COMPLETED":    {"ARCHIVED"},
    "ARCHIVED":     {"DISCOVERY"},
}

@dataclass
class ProjetoEntity:
    usuario_id: int
    cliente_id: int
    servico_id: int
    id: int | None = None
    status: str = 'DISCOVERY'
    data_entrega: date | None = None
    valor: Decimal | None = None
    valor_mensal: Decimal | None = None
    dia_vencimento: int = 5
    recorrencia_inicio: date | None = None
    tipo_recorrencia: str = 'AVULSO'
    recorrencia_ativa: bool = False
    criado_em: datetime | None = None
    deletado_em: datetime | None = None

    def validate(self) -> None:
        """Valida as regras de consistência da entidade."""
        if self.valor is not None and self.valor <= 0:
            raise ValidaEntidadeException("O valor do contrato deve ser maior que zero.")
        if self.status not in VALID_STATUSES:
            raise ValidaEntidadeException(f"Status inválido: {self.status}")
        if self.tipo_recorrencia not in VALID_RECURRENCE_TYPES:
            raise ValidaEntidadeException(
                f"Tipo de recorrência inválido: {self.tipo_recorrencia}"
            )

        if self.tipo_recorrencia == "MENSAL":
            if self.valor_mensal is None or self.valor_mensal <= 0:
                raise ValidaEntidadeException(
                    "Projetos mensais devem possuir um valor mensal maior que zero."
                )
            if not (1 <= self.dia_vencimento <= 28):
                raise ValidaEntidadeException(
                    "O dia de vencimento para recorrências deve estar entre 1 e 28."
                )
            if self.status in {"COMPLETED", "ARCHIVED"} and self.recorrencia_ativa:
                raise ValidaEntidadeException(
                    "Projetos concluídos ou arquivados não podem possuir recorrência ativa."
                )
        else:
            if self.recorrencia_ativa:
                raise ValidaEntidadeException(
                    "Projetos avulsos não podem possuir recorrência ativa."
                )
            if self.valor_mensal is not None:
                raise ValidaEntidadeException(
                    "Projetos avulsos não podem possuir valor mensal."
                )

    def validate_transition(self, new_status: str) -> None:
        if new_status not in STATUS_TRANSITIONS.get(self.status, set()):
            raise ValidaEntidadeException(
                f"Transição de status inválida: {self.status} -> {new_status}"
            )

    def change_status(self, new_status: str) -> None:
        """Aplica uma transição e mantém as invariantes do ciclo de vida."""
        if new_status == self.status:
            return
        self.validate_transition(new_status)
        self.status = new_status
        if new_status in {"COMPLETED", "ARCHIVED"}:
            self.recorrencia_ativa = False

    @property
    def is_deleted(self) -> bool:
        return self.deletado_em is not None
