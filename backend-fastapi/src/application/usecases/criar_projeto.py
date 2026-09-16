from decimal import Decimal
from datetime import date
from src.domain.entities.projeto import ProjetoEntity
from src.domain.exceptions.business_exceptions import ColisaoContratoException, ValidaEntidadeException
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.application.ports.outbound.i_cliente_repository import IClienteRepository
from src.application.ports.outbound.i_servico_repository import IServicoRepository

class CriarProjetoUseCase:
    def __init__(
        self,
        projeto_repo: IProjetoRepository,
        cliente_repo: IClienteRepository,
        servico_repo: IServicoRepository
    ):
        self.projeto_repo = projeto_repo
        self.cliente_repo = cliente_repo
        self.servico_repo = servico_repo

    async def execute(
        self,
        usuario_id: int,
        cliente_id: int,
        servico_id: int,
        status: str = 'DISCOVERY',
        progresso: int = 0,
        data_entrega: date | None = None,
        valor: Decimal | None = None,
        tipo_recorrencia: str = 'AVULSO',
        recorrencia_ativa: bool = False,
        valor_mensal: Decimal | None = None,
        dia_vencimento: int = 5,
        recorrencia_inicio: date | None = None
    ) -> ProjetoEntity:
        # 1. Verifica se cliente pertence ao usuário
        cliente_existe = await self.cliente_repo.exists_by_id(cliente_id, usuario_id)
        if not cliente_existe:
            raise ValidaEntidadeException("Cliente não encontrado ou não pertence a você.")

        # 2. Verifica se serviço pertence ao usuário
        servico_existe = await self.servico_repo.exists_by_id(servico_id, usuario_id)
        if not servico_existe:
            raise ValidaEntidadeException("Serviço não encontrado ou não pertence a você.")

        # 3. Verifica colisão de contrato ativo
        colisao = await self.projeto_repo.exists_active_contract(cliente_id, servico_id)
        if colisao:
            raise ColisaoContratoException("Este cliente já possui este serviço contratado de forma ativa.")

        # 4. Instancia e valida a entidade
        tipo_recorrencia = tipo_recorrencia.strip().upper()
        projeto = ProjetoEntity(
            usuario_id=usuario_id,
            cliente_id=cliente_id,
            servico_id=servico_id,
            status=status,
            progresso=progresso,
            data_entrega=data_entrega,
            valor=valor,
            tipo_recorrencia=tipo_recorrencia,
            recorrencia_ativa=recorrencia_ativa,
            valor_mensal=valor_mensal,
            dia_vencimento=dia_vencimento,
            recorrencia_inicio=recorrencia_inicio
        )
        projeto.validate()

        # 5. Salva na persistência
        projeto_salvo = await self.projeto_repo.save(projeto)

        return projeto_salvo
