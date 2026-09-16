"""Preserve legacy service data and introduce rich descriptions and reusable tags."""
from alembic import op
import sqlalchemy as sa

revision = "20260916_0002"
down_revision = "20260905_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("servicos", sa.Column("descricao_documento", sa.JSON(), nullable=True))
    tags = op.create_table(
        "tags", sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False),
        sa.Column("nome", sa.String(40), nullable=False),
        sa.Column("nome_normalizado", sa.String(120), nullable=False),
        sa.UniqueConstraint("usuario_id", "nome_normalizado", name="uq_tag_usuario_nome"),
    )
    links = op.create_table(
        "servico_tags",
        sa.Column("servico_id", sa.Integer(), sa.ForeignKey("servicos.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.Integer(), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )
    services = sa.table("servicos", sa.column("id"), sa.column("usuario_id"), sa.column("descricao"),
                        sa.column("tags"), sa.column("descricao_documento", sa.JSON()))
    connection = op.get_bind()
    catalog = {}
    for service in connection.execute(sa.select(services)).mappings().all():
        if service["descricao"]:
            doc = {"version": 1, "doc": {"type": "doc", "content": [
                {"type": "paragraph", "content": [{"type": "text", "text": line}] if line else []}
                for line in service["descricao"].splitlines()
            ]}}
            connection.execute(services.update().where(services.c.id == service["id"]).values(descricao_documento=doc))
        used = set()
        for raw in (service["tags"] or "").split(","):
            name = " ".join(raw.split())
            if not name:
                continue
            # Legacy text remains intact in servicos.tags; names above the new
            # limit are truncated only in the new selectable catalog.
            name = name[:40]
            key = (service["usuario_id"], name.casefold())
            if key not in catalog:
                result = connection.execute(tags.insert().values(usuario_id=key[0], nome=name, nome_normalizado=key[1]))
                catalog[key] = result.inserted_primary_key[0]
            tag_id = catalog[key]
            if tag_id not in used:
                connection.execute(links.insert().values(servico_id=service["id"], tag_id=tag_id))
                used.add(tag_id)


def downgrade():
    op.drop_table("servico_tags")
    op.drop_table("tags")
    op.drop_column("servicos", "descricao_documento")
