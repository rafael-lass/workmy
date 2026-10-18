import pytest
from decimal import Decimal
from src.domain.entities.projeto import ProjetoEntity
from src.domain.exceptions.business_exceptions import ValidaEntidadeException

def test_projeto_entity_validation_success():
    projeto = ProjetoEntity(
        usuario_id=1,
        cliente_id=1,
        servico_id=1,
        valor=Decimal("1500.00"),
        dia_vencimento=10
    )
    # Não deve levantar exceção
    projeto.validate()

def test_projeto_entity_validation_invalid_valor():
    projeto = ProjetoEntity(
        usuario_id=1,
        cliente_id=1,
        servico_id=1,
        valor=Decimal("-10.00"),
        dia_vencimento=10
    )
    with pytest.raises(ValidaEntidadeException) as exc:
        projeto.validate()
    assert "O valor do contrato deve ser maior que zero" in str(exc.value)

def test_projeto_entity_validation_invalid_dia_vencimento():
    projeto = ProjetoEntity(
        usuario_id=1,
        cliente_id=1,
        servico_id=1,
        valor=Decimal("100.00"),
        tipo_recorrencia="MENSAL",
        valor_mensal=Decimal("100.00"),
        dia_vencimento=30,
    )
    with pytest.raises(ValidaEntidadeException) as exc:
        projeto.validate()
    assert "O dia de vencimento para recorrências deve estar entre 1 e 28" in str(exc.value)

def test_completed_project_cannot_keep_active_recurrence():
    projeto = ProjetoEntity(
        usuario_id=1,
        cliente_id=1,
        servico_id=1,
        status="COMPLETED",
        tipo_recorrencia="MENSAL",
        recorrencia_ativa=True,
        valor_mensal=Decimal("100.00"),
    )

    with pytest.raises(ValidaEntidadeException):
        projeto.validate()
