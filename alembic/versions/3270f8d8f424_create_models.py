"""create models

Revision ID: 3270f8d8f424
Revises: 
Create Date: 2024-12-11 14:37:36.549201

"""
from typing import Sequence, Union
import geoalchemy2
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '3270f8d8f424'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('camp',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('camp_name', sa.String(length=50), nullable=False),
                    sa.Column('city', sa.String(length=50), nullable=False),
                    sa.Column('geo_location',
                              geoalchemy2.types.Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromEWKT',
                                                         name='geometry', nullable=False), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('camp')
    # ### end Alembic commands ###
