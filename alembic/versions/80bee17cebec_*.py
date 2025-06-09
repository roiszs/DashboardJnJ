"""Añadir campos asociados y supervisor

Revision ID: 80bee17cebec
Revises: 
Create Date: 2025-06-09 03:28:49.957700

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '80bee17cebec'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Añadimos las nuevas columnas sin tocar la tabla existente
    op.add_column(
        'eficiencias',
        sa.Column('nombre_asociado', sa.String(), nullable=False)
    )
    op.add_column(
        'eficiencias',
        sa.Column('wwid', sa.Integer(), nullable=False)
    )
    op.add_column(
        'eficiencias',
        sa.Column('supervisor', sa.String(), nullable=False)
    )
    op.add_column(
        'eficiencias',
        sa.Column('numero_batch', sa.String(), nullable=False)
    )
    op.add_column(
        'eficiencias',
        sa.Column('eficiencia_asociado', sa.Float(), nullable=False)
    )
    op.add_column(
        'eficiencias',
        sa.Column('eficiencia_linea', sa.Float(), nullable=True)
    )

    # Índices opcionales para acelerar consultas por asociado o WWID
    op.create_index(
        'ix_eficiencias_nombre_asociado',
        'eficiencias',
        ['nombre_asociado'],
        unique=False
    )
    op.create_index(
        'ix_eficiencias_wwid',
        'eficiencias',
        ['wwid'],
        unique=False
    )


def downgrade() -> None:
    # Eliminamos en orden inverso para poder revertir sin errores
    op.drop_index('ix_eficiencias_wwid', table_name='eficiencias')
    op.drop_index('ix_eficiencias_nombre_asociado', table_name='eficiencias')

    op.drop_column('eficiencias', 'eficiencia_linea')
    op.drop_column('eficiencias', 'eficiencia_asociado')
    op.drop_column('eficiencias', 'numero_batch')
    op.drop_column('eficiencias', 'supervisor')
    op.drop_column('eficiencias', 'wwid')
    op.drop_column('eficiencias', 'nombre_asociado')
