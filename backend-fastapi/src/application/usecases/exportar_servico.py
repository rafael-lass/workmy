from src.application.ports.outbound.i_servico_repository import IServicoRepository
from src.domain.exceptions.business_exceptions import NaoEncontradoException
from src.domain.service_document import validate_document


class ExportarServicoUseCase:
    def __init__(self, repository: IServicoRepository):
        self.repository = repository

    async def preparar(self, servico_id: int, usuario_id: int, contact: dict):
        service = await self.repository.get_by_id(servico_id, usuario_id)
        if service is None:
            raise NaoEncontradoException("Serviço não encontrado.")
        service.descricao_documento = validate_document(service.descricao_documento)
        return service, contact
