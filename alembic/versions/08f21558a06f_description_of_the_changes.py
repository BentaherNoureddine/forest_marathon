"""Description of the changes

Revision ID: 08f21558a06f
Revises: b71ddd89eba2
Create Date: 2024-12-12 13:18:50.765546

"""
from typing import Sequence, Union

import geoalchemy2
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08f21558a06f'
down_revision: Union[str, None] = 'b71ddd89eba2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('users', 'password', type_=sa.String(60), existing_type=sa.String(100))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('users')
    op.drop_table('camp')
    # ### end Alembic commands ###