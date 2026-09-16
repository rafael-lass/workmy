from abc import ABC, abstractmethod
from src.domain.entities.projeto import ProjetoEntity
from src.application.dto.views import ProjetoView

class IProjetoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int, usuario_id: int) -> ProjetoEntity | None:
        pass

    @abstractmethod
    async def list_by_usuario(self, usuario_id: int, cliente_id: int | None = None) -> list[ProjetoEntity]:
        pass

    @abstractmethod
    async def save(self, projeto: ProjetoEntity) -> ProjetoEntity:
        pass

    @abstractmethod
    async def exists_active_contract(self, cliente_id: int, servico_id: int, exclude_id: int | None = None) -> bool:
        pass

    @abstractmethod
    async def list_recorrentes_ativos(self, usuario_id: int) -> list[ProjetoEntity]:
        pass

    @abstractmethod
    async def list_with_names(self, usuario_id: int, cliente_id: int | None = None) -> list[ProjetoView]:
        pass

    @abstractmethod
    async def get_with_names(self, projeto_id: int, usuario_id: int) -> ProjetoView | None:
        pass

    @abstractmethod
    async def count_lancamentos(self, projeto_id: int) -> int:
        pass
