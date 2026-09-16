from datetime import date, timedelta
from decimal import Decimal

import pytest

from src.domain.entities.pagamento import PagamentoEntity
from src.domain.exceptions.business_exceptions import ValidaEntidadeException
from src.domain.time import business_today


def mensalidade(status: str = "PENDENTE") -> PagamentoEntity:
    return PagamentoEntity(
        projeto_id=1,
        valor=Decimal("500.00"),
        data_vencimento=date(2026, 5, 5),
        tipo_pagamento="MENSAL",
        status=status,
        referencia_mes="2026-05",
        gerado_automaticamente=True,
        data_pagamento=date(2026, 5, 5) if status in {"PAGO", "ESTORNADO"} else None,
        motivo_ajuste="Correção contábil" if status == "ESTORNADO" else None,
    )


def test_mensalidade_pendente_valida():
    mensalidade().validate()


def test_rejeita_valor_invalido():
    pagamento = PagamentoEntity(
        projeto_id=1,
        valor=Decimal("-5.00"),
        data_vencimento=date(2026, 5, 26),
        data_pagamento=date(2026, 5, 26),
    )
    with pytest.raises(ValidaEntidadeException, match="maior que zero"):
        pagamento.validate()


@pytest.mark.parametrize("referencia", ["26-05", "2026-13"])
def test_rejeita_referencia_mensal_invalida(referencia: str):
    pagamento = mensalidade()
    pagamento.referencia_mes = referencia
    with pytest.raises(ValidaEntidadeException):
        pagamento.validate()


def test_rejeita_data_de_recebimento_futura():
    pagamento = PagamentoEntity(
        projeto_id=1,
        valor=Decimal("100.00"),
        data_vencimento=business_today(),
        data_pagamento=business_today() + timedelta(days=1),
    )
    with pytest.raises(ValidaEntidadeException, match="futuro"):
        pagamento.validate()


def test_fluxo_pendente_pago_estornado_e_terminal():
    pagamento = mensalidade()
    pagamento.receber(date(2026, 5, 7))
    assert pagamento.status == "PAGO"
    assert pagamento.data_pagamento == date(2026, 5, 7)

    pagamento.estornar("Cobrança indevida")
    assert pagamento.status == "ESTORNADO"
    assert pagamento.motivo_ajuste == "Cobrança indevida"

    with pytest.raises(ValidaEntidadeException, match="confirmados"):
        pagamento.estornar("Novamente")


def test_cancelamento_exige_pendencia_e_motivo():
    pagamento = mensalidade()
    with pytest.raises(ValidaEntidadeException, match="motivo"):
        pagamento.cancelar("  ")

    pagamento = mensalidade()
    pagamento.cancelar("Contrato encerrado")
    assert pagamento.status == "CANCELADO"
    with pytest.raises(ValidaEntidadeException, match="pendentes"):
        pagamento.receber(date(2026, 5, 7))


def test_atraso_e_calculado_somente_para_pendencia():
    pagamento = mensalidade()
    assert pagamento.em_atraso(date(2026, 5, 6)) is True
    pagamento.receber(date(2026, 5, 6))
    assert pagamento.em_atraso(date(2026, 5, 7)) is False
