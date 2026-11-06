"""crear tablas iniciales de la jerarquia ENCA

Migración inicial (tarea 12, tasks.md) de la Spec enca-strategy-tracking.

Crea las cinco tablas de la jerarquía confirmada de la ENCA 2030
(D-001..D-004; design.md "Data Models") mediante migración versionada de
Alembic (tech.md §10) generada con ``alembic revision --autogenerate`` a partir
de ``Base.metadata`` (no se escribe SQL manual).

Orden de creación según dependencia de claves foráneas:

    ejes → metas → objetivos → indicadores → actividades

Cada tabla define:

- ``id``: clave primaria entera autoincremental (design.md
  "Identificadores — TECHNICAL_DECISION").
- Solo las columnas **confirmadas** de cada entidad. No se incluye ningún
  atributo PENDING_VALIDATION de Indicador ni de Actividad (Req 9.1, 9.2).
- Para las entidades hijas, una clave foránea NOT NULL al padre inmediato,
  con integridad referencial en PostgreSQL (Req 8.1, 8.4).

``downgrade`` revierte en el orden inverso (hijas → padres) para respetar las
restricciones de clave foránea.

Revision ID: 274415e7d992
Revises:
Create Date: 2026-10-02 00:10:58.763518
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '274415e7d992'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tablas creadas en orden de dependencia (padre antes que hija) para que
    # cada FK NOT NULL pueda referenciar una tabla ya existente.
    op.create_table(
        'ejes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'metas',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('descripcion', sa.String(), nullable=False),
        sa.Column('eje_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['eje_id'], ['ejes.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'objetivos',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('descripcion', sa.String(), nullable=False),
        sa.Column('meta_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['meta_id'], ['metas.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'indicadores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=False),
        sa.Column('objetivo_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['objetivo_id'], ['objetivos.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'actividades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('descripcion', sa.String(), nullable=False),
        sa.Column('indicador_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['indicador_id'], ['indicadores.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    # Orden inverso al de creación (hijas antes que padres) para no violar las
    # restricciones de clave foránea al eliminar las tablas.
    op.drop_table('actividades')
    op.drop_table('indicadores')
    op.drop_table('objetivos')
    op.drop_table('metas')
    op.drop_table('ejes')
