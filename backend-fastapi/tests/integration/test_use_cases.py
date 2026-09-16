import pytest
from decimal import Decimal
from datetime import date
from src.domain.entities.projeto import ProjetoEntity
from src.domain.entities.cliente import ClienteEntity
from src.domain.entities.servico import ServicoEntity
from src.domain.entities.pagamento import PagamentoEntity
from src.domain.exceptions.business_exceptions import ColisaoContratoException, ConflitoDeletarException, ValidaEntidadeException
from src.application.usecases.criar_projeto import CriarProjetoUseCase
from src.application.usecases.faturar_recorrencias import FaturarRecorrenciasUseCase
from src.application.usecases.crud_pagamento import CrudPagamentoUseCase
from src.application.usecases.atualizar_projeto import AtualizarProjetoUseCase
from src.application.usecases.deletar_projeto import DeletarProjetoUseCase
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.application.ports.outbound.i_cliente_repository import IClienteRepository
from src.application.ports.outbound.i_servico_repository import IServicoRepository
from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository

# --- MOCKS EM MEMÓRIA ---

class InMemoryClienteRepository(IClienteRepository):
    def __init__(self):
        self.clientes = {}

    async def get_by_id(self, id: int, usuario_id: int) -> ClienteEntity | None:
        return self.clientes.get((id, usuario_id))

    async def list_by_usuario(self, usuario_id: int) -> list[ClienteEntity]:
        return [c for c in self.clientes.values() if c.usuario_id == usuario_id]

    async def save(self, cliente: ClienteEntity) -> ClienteEntity:
        if cliente.id is None:
            cliente.id = len(self.clientes) + 1
        self.clientes[(cliente.id, cliente.usuario_id)] = cliente
        return cliente

    async def exists_by_id(self, id: int, usuario_id: int) -> bool:
        return (id, usuario_id) in self.clientes

    async def exists_by_name(self, nome: str, usuario_id: int) -> bool:
        return any(c.nome == nome and c.usuario_id == usuario_id for c in self.clientes.values())

    async def count_projetos_ativos(self, cliente_id: int, usuario_id: int) -> int:
        return 0

    async def list_with_totals(self, usuario_id: int) -> list:
        return []


class InMemoryServicoRepository(IServicoRepository):
    def __init__(self):
        self.servicos = {}

    async def get_by_id(self, id: int, usuario_id: int) -> ServicoEntity | None:
        return self.servicos.get((id, usuario_id))

    async def list_by_usuario(self, usuario_id: int) -> list[ServicoEntity]:
        return [s for s in self.servicos.values() if s.usuario_id == usuario_id]

    async def save(self, servico: ServicoEntity) -> ServicoEntity:
        if servico.id is None:
            servico.id = len(self.servicos) + 1
        self.servicos[(servico.id, servico.usuario_id)] = servico
        return servico

    async def exists_by_id(self, id: int, usuario_id: int) -> bool:
        return (id, usuario_id) in self.servicos

    async def exists_by_name(self, nome: str, usuario_id: int) -> bool:
        return any(s.nome == nome and s.usuario_id == usuario_id for s in self.servicos.values())

    async def count_projetos_ativos(self, servico_id: int, usuario_id: int) -> int:
        return 0


class InMemoryProjetoRepository(IProjetoRepository):
    def __init__(self):
        self.projetos = []
        self.lancamentos: set[int] = set()

    async def soft_delete(self, id: int, usuario_id: int) -> bool:
        for p in self.projetos:
            if p.id == id and p.usuario_id == usuario_id:
                p.deletado_em = date.today()
                return True
        return False

    async def get_with_names(self, projeto_id: int, usuario_id: int):
        return None

    async def list_with_names(self, usuario_id: int, cliente_id: int | None = None) -> list:
        return []

    async def count_lancamentos(self, projeto_id: int) -> int:
        return int(projeto_id in self.lancamentos)

    async def get_by_id(self, id: int, usuario_id: int) -> ProjetoEntity | None:
        for p in self.projetos:
            if p.id == id and p.usuario_id == usuario_id:
                return p
        return None

    async def list_by_usuario(self, usuario_id: int, cliente_id: int | None = None) -> list[ProjetoEntity]:
        result = [p for p in self.projetos if p.usuario_id == usuario_id]
        if cliente_id is not None:
            result = [p for p in result if p.cliente_id == cliente_id]
        return result

    async def save(self, projeto: ProjetoEntity) -> ProjetoEntity:
        if projeto.id is None:
            projeto.id = len(self.projetos) + 1
        else:
            self.projetos = [p for p in self.projetos if p.id != projeto.id]
        self.projetos.append(projeto)
        return projeto

    async def exists_active_contract(self, cliente_id: int, servico_id: int, exclude_id: int | None = None) -> bool:
        for p in self.projetos:
            if p.id == exclude_id:
                continue
            if p.cliente_id == cliente_id and p.servico_id == servico_id and p.deletado_em is None:
                return True
        return False

    async def list_recorrentes_ativos(self, usuario_id: int) -> list[ProjetoEntity]:
        return [
            p for p in self.projetos
            if p.usuario_id == usuario_id
            and p.tipo_recorrencia == 'MENSAL'
            and p.recorrencia_ativa
            and p.status not in {'COMPLETED', 'ARCHIVED'}
        ]


class InMemoryPagamentoRepository(IPagamentoRepository):
    def __init__(self):
        self.pagamentos = []

    async def get_by_id(self, id: int, usuario_id: int) -> PagamentoEntity | None:
        for pag in self.pagamentos:
            if pag.id == id:
                return pag
        return None

    async def save(self, pagamento: PagamentoEntity) -> PagamentoEntity:
        if pagamento.id is None:
            pagamento.id = len(self.pagamentos) + 1
        else:
            self.pagamentos = [p for p in self.pagamentos if p.id != pagamento.id]
        self.pagamentos.append(pagamento)
        return pagamento

    async def list_with_names(
        self, usuario_id: int, filters: dict, page: int, page_size: int
    ) -> tuple[list, int]:
        return [], 0

    async def save_recorrencia(self, pagamento: PagamentoEntity) -> PagamentoEntity | None:
        for pag in self.pagamentos:
            if pag.projeto_id == pagamento.projeto_id and pag.referencia_mes == pagamento.referencia_mes:
                return None
        return await self.save(pagamento)

    async def sum_recebido_mes(self, usuario_id: int, ano: int, mes: int) -> Decimal:
        return Decimal("0.00")

    async def count_recebido_mes(self, usuario_id: int, ano: int, mes: int) -> int:
        return 0


# --- TESTES ---

@pytest.mark.asyncio
async def test_criar_projeto_use_case_success():
    cliente_repo = InMemoryClienteRepository()
    servico_repo = InMemoryServicoRepository()
    projeto_repo = InMemoryProjetoRepository()

    # Prepara dados
    await cliente_repo.save(ClienteEntity(id=1, usuario_id=10, nome="Cliente A"))
    await servico_repo.save(ServicoEntity(id=2, usuario_id=10, nome="Servico B"))

    use_case = CriarProjetoUseCase(projeto_repo, cliente_repo, servico_repo)

    projeto = await use_case.execute(
        usuario_id=10,
        cliente_id=1,
        servico_id=2,
        valor=Decimal("2000.00"),
        tipo_recorrencia='MENSAL',
        recorrencia_ativa=True,
        valor_mensal=Decimal("500.00"),
        dia_vencimento=5
    )

    assert projeto.id == 1
    assert projeto.usuario_id == 10
    assert projeto.valor == Decimal("2000.00")
    assert projeto.tipo_recorrencia == "MENSAL"
    assert projeto.recorrencia_ativa is True


@pytest.mark.asyncio
async def test_criar_projeto_use_case_colisao():
    cliente_repo = InMemoryClienteRepository()
    servico_repo = InMemoryServicoRepository()
    projeto_repo = InMemoryProjetoRepository()

    await cliente_repo.save(ClienteEntity(id=1, usuario_id=10, nome="Cliente A"))
    await servico_repo.save(ServicoEntity(id=2, usuario_id=10, nome="Servico B"))

    # Salva projeto ativo anterior
    await projeto_repo.save(ProjetoEntity(usuario_id=10, cliente_id=1, servico_id=2))

    use_case = CriarProjetoUseCase(projeto_repo, cliente_repo, servico_repo)

    with pytest.raises(ColisaoContratoException):
        await use_case.execute(
            usuario_id=10,
            cliente_id=1,
            servico_id=2
        )


@pytest.mark.asyncio
async def test_faturar_recorrencias_use_case():
    projeto_repo = InMemoryProjetoRepository()
    pagamento_repo = InMemoryPagamentoRepository()

    # Prepara contratos mensalistas
    # Projeto 1: Dia vencimento 5, elegível
    await projeto_repo.save(ProjetoEntity(
        id=1, usuario_id=10, cliente_id=1, servico_id=1,
        tipo_recorrencia='MENSAL', recorrencia_ativa=True,
        valor_mensal=Decimal("500.00"), dia_vencimento=5,
        recorrencia_inicio=date(2026, 5, 1),
    ))
    # Projeto 2: Dia vencimento 28, NÃO elegível (hoje é dia 15)
    await projeto_repo.save(ProjetoEntity(
        id=2, usuario_id=10, cliente_id=1, servico_id=2,
        tipo_recorrencia='MENSAL', recorrencia_ativa=True,
        valor_mensal=Decimal("1000.00"), dia_vencimento=28,
        recorrencia_inicio=date(2026, 5, 1),
    ))

    use_case = FaturarRecorrenciasUseCase(projeto_repo, pagamento_repo)

    # Executa simulando data 2026-05-15 (dia 15)
    hoje = date(2026, 5, 15)
    pagamentos = await use_case.execute(usuario_id=10, hoje=hoje)

    assert len(pagamentos) == 1
    assert pagamentos[0].projeto_id == 1
    assert pagamentos[0].valor == Decimal("500.00")
    assert pagamentos[0].referencia_mes == "2026-05"

    # A mesma referência é idempotente.
    repeticao = await use_case.execute(usuario_id=10, hoje=hoje)
    assert repeticao == []


@pytest.mark.asyncio
async def test_faturar_recorrencias_ignora_inicio_futuro_e_projeto_encerrado():
    projeto_repo = InMemoryProjetoRepository()
    pagamento_repo = InMemoryPagamentoRepository()

    await projeto_repo.save(ProjetoEntity(
        id=1, usuario_id=10, cliente_id=1, servico_id=1,
        tipo_recorrencia='MENSAL', recorrencia_ativa=True,
        valor_mensal=Decimal("500.00"), dia_vencimento=5,
        recorrencia_inicio=date(2026, 6, 1),
    ))
    await projeto_repo.save(ProjetoEntity(
        id=2, usuario_id=10, cliente_id=1, servico_id=2,
        status='COMPLETED', progresso=100,
        tipo_recorrencia='MENSAL', recorrencia_ativa=True,
        valor_mensal=Decimal("800.00"), dia_vencimento=5,
    ))

    use_case = FaturarRecorrenciasUseCase(projeto_repo, pagamento_repo)
    pagamentos = await use_case.execute(usuario_id=10, hoje=date(2026, 5, 15))

    assert pagamentos == []


@pytest.mark.asyncio
async def test_pagamento_manual_e_sempre_avulso():
    projeto_repo = InMemoryProjetoRepository()
    pagamento_repo = InMemoryPagamentoRepository()
    await projeto_repo.save(ProjetoEntity(
        id=1, usuario_id=10, cliente_id=1, servico_id=1,
    ))

    use_case = CrudPagamentoUseCase(pagamento_repo, projeto_repo)
    pagamento = await use_case.criar(
        projeto_id=1,
        usuario_id=10,
        valor=Decimal("250.00"),
        data_pagamento=date(2026, 5, 15),
    )

    assert pagamento.tipo_pagamento == "AVULSO"
    assert pagamento.status == "PAGO"
    assert pagamento.data_vencimento == date(2026, 5, 15)
    assert pagamento.referencia_mes is None
    assert pagamento.gerado_automaticamente is False


@pytest.mark.asyncio
async def test_atualizar_projeto_limpa_opcional_e_encerra_recorrencia():
    projeto_repo = InMemoryProjetoRepository()
    await projeto_repo.save(ProjetoEntity(
        id=1,
        usuario_id=10,
        cliente_id=1,
        servico_id=1,
        valor=Decimal("1000.00"),
        tipo_recorrencia="MENSAL",
        recorrencia_ativa=True,
        valor_mensal=Decimal("300.00"),
    ))
    use_case = AtualizarProjetoUseCase(projeto_repo)

    projeto = await use_case.execute(1, 10, {"valor": None, "status": "IN_PROGRESS"})
    assert projeto.valor is None

    await use_case.execute(1, 10, {"status": "REVIEW"})
    projeto = await use_case.execute(1, 10, {"status": "COMPLETED", "progresso": 40})
    assert projeto.progresso == 100
    assert projeto.recorrencia_ativa is False


@pytest.mark.asyncio
async def test_pausa_e_retomada_nao_geram_meses_pausados():
    projeto_repo = InMemoryProjetoRepository()
    pagamento_repo = InMemoryPagamentoRepository()
    await projeto_repo.save(ProjetoEntity(
        id=1,
        usuario_id=10,
        cliente_id=1,
        servico_id=1,
        tipo_recorrencia="MENSAL",
        recorrencia_ativa=True,
        valor_mensal=Decimal("300.00"),
        dia_vencimento=5,
        recorrencia_inicio=date(2026, 1, 1),
    ))
    billing = FaturarRecorrenciasUseCase(projeto_repo, pagamento_repo)
    updater = AtualizarProjetoUseCase(projeto_repo)

    first = await billing.execute(10, date(2026, 2, 15))
    assert [item.referencia_mes for item in first] == ["2026-01", "2026-02"]

    await updater.execute(1, 10, {"recorrencia_ativa": False})
    assert await billing.execute(10, date(2026, 3, 15)) == []

    await updater.execute(1, 10, {
        "recorrencia_ativa": True,
        "valor_mensal": Decimal("350.00"),
        "dia_vencimento": 5,
        "recorrencia_inicio": date(2026, 4, 1),
    })
    resumed = await billing.execute(10, date(2026, 4, 15))
    assert [item.referencia_mes for item in resumed] == ["2026-04"]
    assert resumed[0].valor == Decimal("350.00")
    assert {item.referencia_mes for item in pagamento_repo.pagamentos} == {
        "2026-01", "2026-02", "2026-04"
    }


@pytest.mark.asyncio
async def test_nao_exclui_projeto_com_historico_financeiro():
    projeto_repo = InMemoryProjetoRepository()
    await projeto_repo.save(ProjetoEntity(id=1, usuario_id=10, cliente_id=1, servico_id=1))
    projeto_repo.lancamentos.add(1)

    with pytest.raises(ConflitoDeletarException, match="histórico financeiro"):
        await DeletarProjetoUseCase(projeto_repo).execute(1, 10)
