from datetime import date
from decimal import Decimal

from src.application.ports.outbound.i_pagamento_repository import IPagamentoRepository
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository
from src.domain.entities.pagamento import PagamentoEntity
from src.domain.exceptions.business_exceptions import NaoEncontradoException


class CrudPagamentoUseCase:
    def __init__(self, pagamento_repo: IPagamentoRepository, projeto_repo: IProjetoRepository):
        self.pagamento_repo = pagamento_repo
        self.projeto_repo = projeto_repo

    async def criar(
        self,
        projeto_id: int,
        usuario_id: int,
        valor: Decimal,
        data_pagamento: date,
        observacao: str | None = None,
        comprovante_bytes: bytes | None = None,
        comprovante_mime: str | None = None,
    ) -> PagamentoEntity:
        if not await self.projeto_repo.get_by_id(projeto_id, usuario_id):
            raise NaoEncontradoException("Projeto não encontrado ou não pertence a você.")

        pagamento = PagamentoEntity(
            projeto_id=projeto_id,
            valor=valor,
            tipo_pagamento="AVULSO",
            status="PAGO",
            data_vencimento=data_pagamento,
            data_pagamento=data_pagamento,
            observacao=observacao,
            comprovante_bytes=comprovante_bytes,
            comprovante_mime=comprovante_mime,
        )
        pagamento.validate()
        return await self.pagamento_repo.save(pagamento)

    async def receber(
        self,
        pagamento_id: int,
        usuario_id: int,
        data_pagamento: date,
        observacao: str | None = None,
        comprovante_bytes: bytes | None = None,
        comprovante_mime: str | None = None,
    ) -> PagamentoEntity:
        pagamento = await self._get(pagamento_id, usuario_id)
        pagamento.receber(
            data_pagamento=data_pagamento,
            observacao=observacao,
            comprovante_bytes=comprovante_bytes,
            comprovante_mime=comprovante_mime,
        )
        return await self.pagamento_repo.save(pagamento)

    async def cancelar(self, pagamento_id: int, usuario_id: int, motivo: str) -> PagamentoEntity:
        pagamento = await self._get(pagamento_id, usuario_id)
        pagamento.cancelar(motivo)
        return await self.pagamento_repo.save(pagamento)

    async def estornar(self, pagamento_id: int, usuario_id: int, motivo: str) -> PagamentoEntity:
        pagamento = await self._get(pagamento_id, usuario_id)
        pagamento.estornar(motivo)
        return await self.pagamento_repo.save(pagamento)

    async def atualizar_detalhes(
        self,
        pagamento_id: int,
        usuario_id: int,
        observacao: str | None,
        comprovante_bytes: bytes | None,
        comprovante_mime: str | None,
    ) -> PagamentoEntity:
        pagamento = await self._get(pagamento_id, usuario_id)
        pagamento.atualizar_detalhes(observacao, comprovante_bytes, comprovante_mime)
        return await self.pagamento_repo.save(pagamento)

    async def _get(self, pagamento_id: int, usuario_id: int) -> PagamentoEntity:
        pagamento = await self.pagamento_repo.get_by_id(pagamento_id, usuario_id)
        if not pagamento:
            raise NaoEncontradoException("Lançamento financeiro não encontrado.")
        return pagamento
