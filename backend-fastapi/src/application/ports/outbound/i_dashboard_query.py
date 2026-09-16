from abc import ABC, abstractmethod
from datetime import date


class IDashboardQuery(ABC):
    @abstractmethod
    async def get_resumo(self, usuario_id: int, hoje: date) -> dict:
        pass
