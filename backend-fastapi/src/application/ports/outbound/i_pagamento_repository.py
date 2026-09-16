from abc import ABC, abstractmethod

from src.application.dto.views import PagamentoView
from src.domain.entities.pagamento import PagamentoEntity


class IPagamentoRepository(ABC):
    @abstractmethod
    async def get_by_id(self, id: int, usuario_id: int) -> PagamentoEntity | None:
        pass

    @abstractmethod
    async def save(self, pagamento: PagamentoEntity) -> PagamentoEntity:
        pass

    @abstractmethod
    async def save_recorrencia(self, pagamento: PagamentoEntity) -> PagamentoEntity | None:
        """Cria uma mensalidade uma única vez por projeto e referência."""
        pass

    @abstractmethod
    async def list_with_names(
        self,
        usuario_id: int,
        filters: dict,
        page: int,
        page_size: int,
    ) -> tuple[list[PagamentoView], int]:
        pass
