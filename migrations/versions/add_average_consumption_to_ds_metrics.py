"""Add average_consumption to DSMetrics

Revision ID: add_avg_consumption
Revises: add_avg_engine_size
Create Date: 2025-12-10 21:30:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "add_avg_consumption"
down_revision = "add_avg_engine_size"
branch_labels = None
depends_on = None


def upgrade():
    # La columna average_consumption ya existe en la base de datos
    # Esta migración solo marca el estado como actualizado
    pass


def downgrade():
    # No hacemos downgrade
    pass
