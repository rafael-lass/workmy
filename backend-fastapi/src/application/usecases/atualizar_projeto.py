from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.domain.entities.projeto import ProjetoEntity
from src.domain.exceptions.business_exceptions import (
    NaoEncontradoException,
    ValidaEntidadeException,
)


class AtualizarProjetoUseCase:
    EDITABLE_FIELDS = {
        "status",
        "progresso",
        "data_entrega",
        "valor",
        "tipo_recorrencia",
        "recorrencia_ativa",
        "valor_mensal",
        "dia_vencimento",
        "recorrencia_inicio",
    }

    def __init__(self, projeto_repo: IProjetoRepository):
        self.projeto_repo = projeto_repo

    async def execute(
        self,
        projeto_id: int,
        usuario_id: int,
        changes: dict,
    ) -> ProjetoEntity:
        projeto = await self.projeto_repo.get_by_id(projeto_id, usuario_id)
        if not projeto:
            raise NaoEncontradoException("Projeto não encontrado ou não pertence a você.")

        unknown_fields = set(changes) - self.EDITABLE_FIELDS
        if unknown_fields:
            raise ValidaEntidadeException("Há campos não permitidos na atualização do projeto.")

        values = dict(changes)
        new_status = values.pop("status", None)

        for required_field in (
            "progresso",
            "tipo_recorrencia",
            "recorrencia_ativa",
            "dia_vencimento",
        ):
            if required_field in values and values[required_field] is None:
                raise ValidaEntidadeException(f"O campo {required_field} não pode ser nulo.")

        for field, value in values.items():
            if field == "tipo_recorrencia":
                value = value.strip().upper()
            setattr(projeto, field, value)

        if projeto.tipo_recorrencia == "AVULSO":
            projeto.recorrencia_ativa = False
            projeto.valor_mensal = None
            projeto.recorrencia_inicio = None

        if new_status is not None:
            projeto.change_status(new_status)

        if projeto.status == "COMPLETED":
            projeto.progresso = 100
        if projeto.status in {"COMPLETED", "ARCHIVED"}:
            projeto.recorrencia_ativa = False

        projeto.validate()
        return await self.projeto_repo.save(projeto)
