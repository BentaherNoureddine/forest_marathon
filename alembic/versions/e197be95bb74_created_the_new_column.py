"""created the new column

Revision ID: e197be95bb74
Revises: 40b168615ec2
Create Date: 2024-12-12 14:11:46.608757
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e197be95bb74'
down_revision: Union[str, None] = '40b168615ec2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('logged_in', sa.Boolean(), nullable=False))


def downgrade() -> None:
    op.drop_column('users', 'logged_in')
