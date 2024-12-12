"""Add new column to table

Revision ID: 40b168615ec2
Revises: 9aec2ea60760
Create Date: 2024-12-12 13:58:06.692931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '40b168615ec2'
down_revision: Union[str, None] = '9aec2ea60760'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('logged_in', sa.Boolean(), nullable=False))


def downgrade() -> None:
    pass
