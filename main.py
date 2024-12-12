from fastapi import FastAPI, Depends, HTTPException, status
from geoalchemy2.functions import ST_DWithin, ST_GeogFromWKB
from geoalchemy2.shape import from_shape
from shapely import Point
from sqlalchemy import select, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from authentication.authentication import router as user_router
from blockchain.Blockchain import Blockchain
from blockchain.blockchain_DTO import TransactionRequest
from database.geodb import get_async_session
from model.User import Base
from model.geomodels import Camp, NearbyCampSchema, CreateCampSchema, CampResponseSchema
from service.service import is_camp_table_empty, wkb_to_coordinates

app = FastAPI()

app.include_router(user_router)



@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}




# load camps endpoint
@app.get("/load-camps")
async def load_camps(db_session: AsyncSession = Depends(get_async_session)):
    try:
        # Query all camps
        result = await db_session.execute(select(Camp))
        camps = result.scalars().all()  # Extract all Camp objects

        return camps  # Return the list of camps

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading camps: {str(e)}")


# get nearby camps endpoint


@app.post("/nearby-camps-by-details")
async def get_nearby_camps_by_details(
        nearby_camps_schema: NearbyCampSchema,
        db_session: AsyncSession = Depends(get_async_session),
):
    city, camp_name, km_within = (
        nearby_camps_schema.city,
        nearby_camps_schema.camp_name,
        nearby_camps_schema.km_within
    )

    # Check if the target camp exists and retrieve its geography
    target_camp_query = select(Camp).where(
        and_(Camp.city == city, Camp.camp_name == camp_name)
    )
    result = await db_session.execute(target_camp_query)
    target_camp = result.scalar_one_or_none()

    # If the target camp is not found, return an error message
    if not target_camp:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Camp with provided details was not found",
        )

    # Extract the geography of the target camp
    target_geography = ST_GeogFromWKB(target_camp.geo_location)

    # Query nearby camps within the specified distance from the target camp
    nearby_camps_query = select(Camp.camp_name).where(
        ST_DWithin(Camp.geo_location, target_geography, 1000 * km_within)
    )
    result = await db_session.execute(nearby_camps_query)
    nearby_camps = result.scalars().all()

    return nearby_camps


# create camp endpoint
@app.post("/create_camp", response_model=CampResponseSchema)
async def create_camp(
        camp: CreateCampSchema,
        db_session: AsyncSession = Depends(get_async_session)
):
    try:
        # Convert (latitude, longitude) to a Shapely Point
        point = Point(camp.geo_location[1], camp.geo_location[0])

        # Convert the Shapely Point to a GeoAlchemy2-compatible format
        geo = from_shape(point, srid=4326)

        # Create the Camp object
        new_camp = Camp(
            camp_name=camp.camp_name,
            city=camp.city,
            geo_location=geo
        )

        # Add to database session and commit
        db_session.add(new_camp)
        await db_session.commit()
        await db_session.refresh(new_camp)

        # Convert geo_location to a JSON-friendly format
        response_data = CampResponseSchema(
            id=new_camp.id,
            camp_name=new_camp.camp_name,
            city=new_camp.city,
            geo_location=wkb_to_coordinates(new_camp.geo_location)
        )
        return response_data  # Return the created camp

    except SQLAlchemyError as e:
        await db_session.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")


# get all camps

@app.get("/get_all_camps")
async def get_all_camps(db_session: AsyncSession = Depends(get_async_session)):
    try:
        # Query to select camps and extract their geography
        result = await db_session.execute(
            select(
                Camp.id,
                Camp.camp_name,
                Camp.city,
                func.ST_AsGeoJSON(func.ST_GeogFromWKB(Camp.geo_location)).label("geojson")
            )
        )

        camps = result.all()

        # Transform the query result into a list of dictionaries
        camps_data = [
            {
                "id": camp.id,
                "camp_name": camp.camp_name,
                "city": camp.city,
                "geo_location": camp.geojson,  # GeoJSON representation of the geography
            }
            for camp in camps
        ]

        return camps_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")





#-----------------------------------------------------------------------------------------------------------------------------





blockchain = Blockchain()


#  GET ALL BLOCKS OF THE BLOCKCHAIN

@app.get("/get_chain")
def get_chain():
    return dict(chain=blockchain.chain, length=len(blockchain.chain))



# ADD TRANSACTION ENDPOINT

@app.post('/add_transaction')
def add_transaction(transaction_data: TransactionRequest):
    # CONVERT THE REQUEST TO A DICTIONARY
    data = transaction_data.dict()

    # CHECK THE INTEGRITY OF THE REQUEST
    if 'sender' not in data or 'receiver' not in data or 'amount' not in data:
        raise HTTPException(status_code=400, detail="Invalid transaction data")

    # CHECK THAT THE SENDER IS NOT THE RECEIVER
    if data['sender'] == data['receiver']:
        raise HTTPException(status_code=400, detail="Sender cannot be the same with receiver")

    # THE AMOUNT MUST BE GREATER THAN 0
    if data['amount'] <= 0:
        raise HTTPException(status_code=400, detail="Transaction amount must be greater than zero")

    # Add the transaction to the current list of transactions to be included in the next mined block
    index = blockchain.add_transaction(data['sender'], data['receiver'], data['amount'])
    response = {'message': f'Transaction added to block {index}'}
    return response
