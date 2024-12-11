from geoalchemy2 import Geometry, WKBElement
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from pydantic import BaseModel, PositiveInt
from database.geodb import Base


# city schema

class Camp(Base):
    __tablename__ = "camp"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    camp_name: Mapped[str] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(50))
    state: Mapped[str] = mapped_column(String(50))
    geo_location: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="POINT", srid=4326, spatial_index=True)
    )


# nearby cities schema

class NearbyCampSchema(BaseModel):
    camp: str
    state: str
    km_within: PositiveInt
