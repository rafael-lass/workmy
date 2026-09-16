import datetime as dt
from src.domain.exceptions.business_exceptions import ConflitoDeletarException, NaoEncontradoException
from src.application.ports.outbound.i_projeto_repository import IProjetoRepository

class DeletarProjetoUseCase:
    def __init__(self, projeto_repo: IProjetoRepository):
        self.projeto_repo = projeto_repo

    async def execute(self, projeto_id: int, usuario_id: int) -> None:
        # 1. Busca o projeto e verifica posse
        projeto = await self.projeto_repo.get_by_id(projeto_id, usuario_id)
        if not projeto:
            raise NaoEncontradoException("Projeto não encontrado ou não pertence a você.")

        if await self.projeto_repo.count_lancamentos(projeto_id):
            raise ConflitoDeletarException(
                "Este projeto possui histórico financeiro e não pode ser excluído. Arquive-o para preservar o livro-caixa."
            )

        # Projetos sem histórico financeiro continuam usando soft delete.
        projeto.deletado_em = dt.datetime.now(dt.timezone.utc).replace(tzinfo=None)
        await self.projeto_repo.save(projeto)
