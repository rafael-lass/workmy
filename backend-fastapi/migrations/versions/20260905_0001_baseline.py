"""Baseline do modelo simplificado do WorkMy."""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260905_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("username"),
    )
    op.create_table(
        "clientes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("empresa", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=True),
        sa.Column("telefone", sa.String(length=20), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("deletado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "servicos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("nome", sa.String(length=150), nullable=False),
        sa.Column("descricao", sa.String(length=500), nullable=True),
        sa.Column("tags", sa.String(length=250), nullable=True),
        sa.Column("ferramentas", sa.String(length=250), nullable=True),
        sa.Column("github_repo", sa.String(length=200), nullable=True),
        sa.Column("imagem_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("imagem_mime", sa.String(length=50), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("deletado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uniq_servico_ativo_usuario_nome",
        "servicos",
        ["usuario_id", "nome"],
        unique=True,
        postgresql_where=sa.text("deletado_em IS NULL"),
        sqlite_where=sa.text("deletado_em IS NULL"),
    )
    op.create_table(
        "projetos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("servico_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("progresso", sa.Integer(), nullable=False),
        sa.Column("data_entrega", sa.Date(), nullable=True),
        sa.Column("valor", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("valor_mensal", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("dia_vencimento", sa.Integer(), nullable=False),
        sa.Column("recorrencia_inicio", sa.Date(), nullable=True),
        sa.Column("tipo_recorrencia", sa.String(length=20), nullable=False),
        sa.Column("recorrencia_ativa", sa.Boolean(), nullable=False),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("deletado_em", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["servico_id"], ["servicos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuarios.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "uniq_projeto_ativo_usuario_cliente_servico",
        "projetos",
        ["usuario_id", "cliente_id", "servico_id"],
        unique=True,
        postgresql_where=sa.text("deletado_em IS NULL"),
        sqlite_where=sa.text("deletado_em IS NULL"),
    )
    op.create_table(
        "pagamentos",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("projeto_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("tipo_pagamento", sa.String(length=10), nullable=False),
        sa.Column("status", sa.String(length=12), nullable=False),
        sa.Column("data_vencimento", sa.Date(), nullable=False),
        sa.Column("data_pagamento", sa.Date(), nullable=True),
        sa.Column("observacao", sa.String(length=500), nullable=True),
        sa.Column("referencia_mes", sa.String(length=7), nullable=True),
        sa.Column("gerado_automaticamente", sa.Boolean(), nullable=False),
        sa.Column("status_alterado_em", sa.DateTime(), nullable=False),
        sa.Column("motivo_ajuste", sa.String(length=500), nullable=True),
        sa.Column("comprovante_bytes", sa.LargeBinary(), nullable=True),
        sa.Column("comprovante_mime", sa.String(length=50), nullable=True),
        sa.Column("criado_em", sa.DateTime(), nullable=False),
        sa.Column("atualizado_em", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["projeto_id"], ["projetos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "projeto_id", "referencia_mes", name="uniq_pagamento_projeto_referencia_mes"
        ),
    )
    op.create_index("ix_pagamentos_data_pagamento", "pagamentos", ["data_pagamento"])
    op.create_index("ix_pagamentos_data_vencimento", "pagamentos", ["data_vencimento"])
    op.create_index("ix_pagamentos_status", "pagamentos", ["status"])


def downgrade() -> None:
    op.drop_index("ix_pagamentos_status", table_name="pagamentos")
    op.drop_index("ix_pagamentos_data_vencimento", table_name="pagamentos")
    op.drop_index("ix_pagamentos_data_pagamento", table_name="pagamentos")
    op.drop_table("pagamentos")
    op.drop_index("uniq_projeto_ativo_usuario_cliente_servico", table_name="projetos")
    op.drop_table("projetos")
    op.drop_index("uniq_servico_ativo_usuario_nome", table_name="servicos")
    op.drop_table("servicos")
    op.drop_table("clientes")
    op.drop_table("usuarios")
