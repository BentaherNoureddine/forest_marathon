from typing import Tuple

from geoalchemy2 import WKBElement
from geoalchemy2.shape import to_shape
from sqlalchemy import select, exists
from sqlalchemy.ext.asyncio import AsyncSession
from model.geomodels import Camp


# check if the camp table is empty or not

async def is_camp_table_empty(db_session: AsyncSession):
    query = select(Camp.id.isnot(None))
    query = select(exists(query))
    result = await db_session.execute(query)
    table_exists = result.scalars().one()

    return not (table_exists)


def wkb_to_coordinates(wkb_element: WKBElement) -> Tuple[float, float]:
    point = to_shape(wkb_element)  # Convert WKBElement to Shapely Point
    return point.y, point.x  # Return as (latitude, longitude)
