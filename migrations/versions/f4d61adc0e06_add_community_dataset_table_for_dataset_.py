"""Add community_dataset table for dataset-community assignments

Revision ID: f4d61adc0e06
Revises: 80a14253dafc
Create Date: 2025-12-07 17:14:12.895406

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f4d61adc0e06"
down_revision = "80a14253dafc"
branch_labels = None
depends_on = None


def upgrade():
    # Create community_dataset junction table
    op.create_table(
        "community_dataset",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("community_id", sa.Integer(), nullable=False),
        sa.Column("dataset_id", sa.Integer(), nullable=False),
        sa.Column("assigned_by", sa.Integer(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["community_id"],
            ["community.id"],
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["data_set.id"],
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("community_id", "dataset_id", name="unique_community_dataset"),
    )


def downgrade():
    # Drop community_dataset table
    op.drop_table("community_dataset")
