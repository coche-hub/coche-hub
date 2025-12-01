"""add dataset_id foreign key to coche

Revision ID: 2470d1fe57e5
Revises: 3fe126403e18
Create Date: 2025-12-01 09:06:50.469956

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2470d1fe57e5'
down_revision = '3fe126403e18'
branch_labels = None
depends_on = None


def upgrade():
    # Add dataset_id column to coche table
    with op.batch_alter_table('coche', schema=None) as batch_op:
        batch_op.add_column(sa.Column('dataset_id', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_coche_dataset_id', 'data_set', ['dataset_id'], ['id'])


def downgrade():
    # Remove dataset_id column from coche table
    with op.batch_alter_table('coche', schema=None) as batch_op:
        batch_op.drop_constraint('fk_coche_dataset_id', type_='foreignkey')
        batch_op.drop_column('dataset_id')
