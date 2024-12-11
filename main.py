from fastapi import FastAPI, Depends, HTTPException, status
from geoalchemy2.functions import ST_DWithin, ST_GeogFromWKB
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
import csv
from authentication.authentication import router as register_router
from database.database import engine
from database.geodb import get_async_session
from model.User import Base
from model.geomodels import City, NearbyCitiesSchema
from service.service import is_city_table_empty

app = FastAPI()

app.include_router(register_router)

# create the tables if they don't exist
Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}





# load cities endpoint
@app.get("/load-cities")
async def load_cities(db_session: AsyncSession = Depends(get_async_session)):
    if await is_city_table_empty(db_session):
        cities = []
        with open("us_cities.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")

            # Skip the first row (header)
            next(csv_reader)

            for row in csv_reader:
                city = City(
                    state_code=row[1],
                    state_name=row[2],
                    city=row[3],
                    county=row[4],
                    geo_location=f"POINT({row[5]} {row[6]})",
                )
                cities.append(city)

            db_session.add_all(cities)
            await db_session.commit()
            return {"message": "Data loaded successfully"}

    return {"message": "Data is already loaded"}


# get nearby cities endpoint


@app.post("/nearby-cities-by-details")
async def get_nearby_cities_by_details(
        nearby_cities_schema: NearbyCitiesSchema,
        db_session: AsyncSession = Depends(get_async_session),
):
    city, county, state_code, km_within = (
        nearby_cities_schema.city,
        nearby_cities_schema.county,
        nearby_cities_schema.state_code,
        nearby_cities_schema.km_within,
    )

    # Check if the target city exists and retrieve its geography
    target_city_query = select(City).where(
        and_(City.city == city, City.state_code == state_code, City.county == county)
    )
    result = await db_session.execute(target_city_query)
    target_city = result.scalar_one_or_none()

    # If the target city is not found, return an error message
    if not target_city:
        raise HTTPException(
            status=status.HTTP_404_NOT_FOUND,
            detail="City with provided details was not found",
        )

    # Extract the geography of the target city
    target_geography = ST_GeogFromWKB(target_city.geo_location)

    # Query nearby cities within the specified distance from the target city
    nearby_cities_query = select(City.city).where(
        ST_DWithin(City.geo_location, target_geography, 1000 * km_within)
    )
    result = await db_session.execute(nearby_cities_query)
    nearby_cities = result.scalars().all()

    return nearby_cities
