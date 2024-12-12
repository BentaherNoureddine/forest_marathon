"""Manually added 'logged_in' column

Revision ID: 211dc3349d49
Revises: e197be95bb74
Create Date: 2024-12-12 14:19:42.067774

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '211dc3349d49'
down_revision: Union[str, None] = 'e197be95bb74'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
