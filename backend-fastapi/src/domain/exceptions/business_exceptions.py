class BusinessException(Exception):
    """Classe base para todas as exceções de negócio da aplicação."""
    pass

class ColisaoContratoException(BusinessException):
    """Exceção levantada quando um cliente tenta recontratar o mesmo serviço ativo."""
    pass

class ValidaEntidadeException(BusinessException):
    """Exceção levantada quando regras de validação síncronas de entidades são violadas."""
    pass

class NaoEncontradoException(BusinessException):
    """Exceção genérica para entidades não encontradas ou acesso negado (404/403)."""
    pass

class ConflitoDeletarException(BusinessException):
    """Exceção quando uma deleção não pode ser concluída devido a entidades dependentes."""
    pass
