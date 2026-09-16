from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, EmailStr
from typing import Optional, Literal, List
from datetime import date
from decimal import Decimal
import re

from src.domain.time import business_today


def _normalize_brazilian_phone(value: Optional[str]) -> Optional[str]:
    if value is None or not value.strip():
        return None

    digits = re.sub(r"\D", "", value)
    if len(digits) == 13 and digits.startswith("55"):
        digits = digits[2:]
    if len(digits) not in (10, 11):
        raise ValueError("Telefone inválido. Use um número brasileiro com DDD.")

    ddd, number = digits[:2], digits[2:]
    if ddd.startswith("0"):
        raise ValueError("DDD inválido para telefone brasileiro.")
    if len(number) == 9:
        if not number.startswith("9"):
            raise ValueError("Celular brasileiro deve iniciar com 9 após o DDD.")
        return f"({ddd}) {number[:5]}-{number[5:]}"
    if number[0] in ("0", "1"):
        raise ValueError("Telefone fixo brasileiro inválido para o DDD informado.")
    return f"({ddd}) {number[:4]}-{number[4:]}"

# ============ SEGURANÇA E AUTH ============

class UserLoginSchema(BaseModel):
    email: str = Field(..., description="E-mail do usuário")
    password: str = Field(..., description="Senha do usuário")

class UserRegisterSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr = Field(..., description="E-mail válido do usuário")  # M8 FIX: valida formato automaticamente
    password: str = Field(..., min_length=6)
    telefone: Optional[str] = None

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_brazilian_phone(value)

class TokenResponseSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserProfileSchema(BaseModel):
    id: int
    username: str
    email: str
    telefone: str | None = None

class AuthResponseSchema(BaseModel):
    access: str = Field(..., description="Access Token (JWT)")
    refresh: str = Field(..., description="Refresh Token (JWT)")
    user: UserProfileSchema

class RefreshTokenInSchema(BaseModel):
    refresh: str

class AccessTokenOutSchema(BaseModel):
    access: str

# ============ CLIENTE ============

class ClienteInSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(..., min_length=1, max_length=100)
    empresa: Optional[str] = Field("Não informada", max_length=100)
    email: Optional[EmailStr] = None
    telefone: Optional[str] = Field(None, max_length=20)

    @field_validator("telefone")
    @classmethod
    def validar_telefone_brasil(cls, value: Optional[str]) -> Optional[str]:
        return _normalize_brazilian_phone(value)


class ClienteOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    empresa: str = "Não informada"
    email: Optional[str] = None
    telefone: Optional[str] = None
    total_acumulado: str = "0.00"
    criado_em: str

# ============ SERVIÇO ============

class ServicoInSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    nome: str = Field(..., min_length=1, max_length=150)
    descricao_documento: dict | None = None
    tag_ids: list[int] = Field(default_factory=list, max_length=10)
    imagem_base64: Optional[str] = None

    @field_validator("descricao_documento")
    @classmethod
    def validar_documento(cls, value):
        from src.domain.service_document import validate_document
        return validate_document(value)


class TagInSchema(BaseModel):
    nome: str = Field(min_length=1, max_length=40)


class TagOutSchema(BaseModel):
    id: int
    nome: str


class ServicoPdfSchema(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    nome_profissional: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telefone: str | None = Field(None, max_length=20)

    @field_validator("telefone")
    @classmethod
    def validar_telefone(cls, value):
        return _normalize_brazilian_phone(value)


class ServicoOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao_documento: dict | None = None
    descricao_resumo: str = ""
    tags: list[TagOutSchema] = Field(default_factory=list)
    imagem_base64: Optional[str] = None
    criado_em: str

# ============ PROJETO ============

ProjectStatus = Literal["DISCOVERY", "IN_PROGRESS", "REVIEW", "COMPLETED", "ARCHIVED"]
RecurrenceType = Literal["MENSAL", "AVULSO"]


class ProjetoInSchema(BaseModel):
    cliente_id: int
    servico_id: int
    tipo_recorrencia: RecurrenceType = "AVULSO"
    ativo: bool = False
    valor: Optional[Decimal] = None
    valor_mensal: Optional[Decimal] = Field(None, gt=0)
    dia_vencimento: int = Field(5, ge=1, le=28)
    recorrencia_inicio: Optional[date] = None

    @model_validator(mode="after")
    def validar_recorrencia(self):
        if self.tipo_recorrencia == "MENSAL" and self.valor_mensal is None:
            raise ValueError("Projetos mensais devem possuir um valor mensal maior que zero.")
        if self.tipo_recorrencia == "AVULSO":
            if self.ativo:
                raise ValueError("Projetos avulsos não podem possuir recorrência ativa.")
            if self.valor_mensal is not None:
                raise ValueError("Projetos avulsos não podem possuir valor mensal.")
        return self

class ProjetoUpdateSchema(BaseModel):
    status: Optional[ProjectStatus] = None
    progresso: Optional[int] = Field(None, ge=0, le=100)
    data_entrega: Optional[date] = None
    valor: Optional[Decimal] = None
    tipo_recorrencia: Optional[RecurrenceType] = None
    ativo: Optional[bool] = None
    valor_mensal: Optional[Decimal] = Field(None, gt=0)
    dia_vencimento: Optional[int] = Field(None, ge=1, le=28)
    recorrencia_inicio: Optional[date] = None


class ProjetoOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    cliente_id: int
    cliente_nome: str
    servico_id: int
    servico_nome: str
    valor: Optional[str] = None
    valor_mensal: Optional[str] = None
    dia_vencimento: int = 5
    recorrencia_inicio: Optional[str] = None
    criado_em: str
    status: str
    progresso: int
    total_acumulado: str = "0.00"
    tipo_recorrencia: str
    ativo: bool
    possui_lancamentos: bool = False

class RecorrenciaInSchema(BaseModel):
    ativo: bool
    valor_mensal: Optional[Decimal] = Field(None, gt=0)
    dia_vencimento: Optional[int] = Field(None, ge=1, le=28)
    recorrencia_inicio: Optional[date] = None

    @model_validator(mode="after")
    def validar_reativacao(self):
        if self.ativo and (
            self.valor_mensal is None
            or self.dia_vencimento is None
            or self.recorrencia_inicio is None
        ):
            raise ValueError(
                "Para ativar a recorrência, informe valor, vencimento e nova data inicial."
            )
        return self


class RecorrenciaOutSchema(BaseModel):
    ativo: bool
    tipo_recorrencia: RecurrenceType
    valor_mensal: Optional[str] = None
    dia_vencimento: int
    recorrencia_inicio: Optional[str] = None


class UpdateStatusSchema(BaseModel):
    status: ProjectStatus


# ============ FINANCEIRO ============

PaymentStatus = Literal["PENDENTE", "PAGO", "CANCELADO", "ESTORNADO"]


class PagamentoInSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    projeto_id: int
    valor: Decimal = Field(..., gt=0)
    data_pagamento: date
    observacao: Optional[str] = Field(None, max_length=500)
    comprovante_base64: Optional[str] = None

    @field_validator("data_pagamento")
    @classmethod
    def validar_data_nao_futura(cls, value: date) -> date:
        if value > business_today():
            raise ValueError("A data do recebimento não pode estar no futuro.")
        return value


class ReceberPagamentoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    data_pagamento: date
    observacao: Optional[str] = Field(None, max_length=500)
    comprovante_base64: Optional[str] = None

    @field_validator("data_pagamento")
    @classmethod
    def validar_data_nao_futura(cls, value: date) -> date:
        if value > business_today():
            raise ValueError("A data do recebimento não pode estar no futuro.")
        return value


class AjustePagamentoSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    motivo: str = Field(..., min_length=3, max_length=500)


class PagamentoDetalhesSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observacao: Optional[str] = Field(None, max_length=500)
    comprovante_base64: Optional[str] = None


class PagamentoOutSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    projeto_id: int
    cliente_id: int
    projeto_cliente_nome: str
    projeto_servico_nome: str
    valor: str
    tipo_pagamento: str
    tipo_pagamento_display: str
    status: PaymentStatus
    em_atraso: bool
    data_vencimento: str
    data_pagamento: Optional[str] = None
    referencia_mes: Optional[str] = None
    gerado_automaticamente: bool
    observacao: Optional[str] = None
    comprovante_base64: Optional[str] = None
    motivo_ajuste: Optional[str] = None
    status_alterado_em: str
    criado_em: str
    atualizado_em: str


class PagamentoListOutSchema(BaseModel):
    items: List[PagamentoOutSchema]
    total: int
    page: int
    page_size: int


# ============ DASHBOARD ============

class DashboardSerieItemSchema(BaseModel):
    mes: str
    total: str


class DashboardResumoOutSchema(BaseModel):
    recebido_mes: str
    pendente_total: str
    atrasado_total: str
    previsto_proximo_mes: str
    projetos_ativos: int
    clientes_total: int
    serie_seis_meses: List[DashboardSerieItemSchema]
    ultimos_recebimentos: List[PagamentoOutSchema]


# ============ SCHEMAS DE ERRO / MENSAGEM ============

class ErrorSchema(BaseModel):
    detail: str


class MessageSchema(BaseModel):
    message: str
