from dotenv.parser import Position
from fastapi import FastAPI, Depends, HTTPException, status
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_DWithin, ST_GeogFromWKB, ST_SetSRID
from geoalchemy2.shape import from_shape
from shapely import Point
from sqlalchemy import select, and_, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from authentication.authentication import router as user_router
from blockchain.Blockchain import Blockchain
from blockchain.blockchain_DTO import TransactionRequest, BalanceRequest
from database.geodb import get_async_session
import copy

from model.User import User
from model.Camp import Camp, NearbyCampSchema, CreateCampSchema, CampResponseSchema
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


# get camp by id

@app.get("/get_camp_by_id/{id}")
async def get_camp_by_id(camp_id: int, db_session: AsyncSession = Depends(get_async_session)):
    try:
        query = await db_session.execute(
            select(
                Camp.id,
                Camp.camp_name,
                Camp.city,
                func.ST_AsGeoJSON(Camp.geo_location).label("geojson")
            ).where(camp_id == Camp.id)
        )
        camp = query.first()

        # If no camp is found
        if not camp:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Camp not found")

        # Return the camp details
        return {
            "id": camp.id,
            "camp_name": camp.camp_name,
            "city": camp.city,
            "geojson": camp.geojson
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while fetching camp details.")


# check if there is nearby camps

@app.get("/nearby_camps/{user_id}")
async def get_nearby_camps(user_id: int, radius: float = 10, db: AsyncSession = Depends(get_async_session)):
    """
    Fetch nearby camps for a user based on their current position.
    - `user_id`: ID of the user
    - `radius`: Radius in meters (default is 10,000 meters or 10 km)
    """
    try:
        # Fetch the user's current position
        user_query = await db.execute(select(User.current_position).where(user_id == User.id))

        user_position = user_query.scalar_one_or_none()

        if not user_position:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found or position not set.")

        # Query nearby camps within the specified radius
        query = await db.execute(
            select(
                Camp.id,
                Camp.camp_name,
                Camp.city,
                func.ST_AsGeoJSON(Camp.geo_location).label("geojson")
            ).where(
                ST_DWithin(
                    Camp.geo_location,
                    func.ST_SetSRID(user_position, 4326),
                    radius
                )
            )
        )

        camps = query.fetchall()

        # Format the response
        result = [
            {
                "id": camp.id,
                "camp_name": camp.camp_name,
                "city": camp.city,
                "geojson": camp.geojson
            }
            for camp in camps
        ]

        return {"user_id": user_id, "nearby_camps": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# Endpoint to add a new balance to the blockchain
@app.post('/add_balance')
def add_balance(balance_data: BalanceRequest):
    data = balance_data.dict()

    # check the integrity of the request
    if 'receiver' not in data or 'amount' not in data:
        raise HTTPException(status_code=400, detail="Invalid transaction data")

    # the amount should be more than 0
    if data['amount'] <= 0:
        raise HTTPException(status_code=400, detail="Balance must be greater than zero")

    # Add the balances to the current list of balances in order to be included in the next mined block
    index = blockchain.add_balance(data['receiver'], data['amount'])
    response = {'message': f'Balance added to block {index}'}
    return response


# -----------------------------------------------------------------------------------------------------------------------------


blockchain = Blockchain()


#  GET INFOS ABOUT A BLOCKCHAIN ENDPOINT

@app.get("/get_chain")
def get_chain():
    return dict(chain=blockchain.chain, length=len(blockchain.chain))


# CHECK THE VALIDITY OF A BLOCKCHAIN ENDPOINT
@app.get('/valid')
def valid():
    if blockchain.is_chain_valid():
        return {'message': 'The Blockchain is valid.'}
    else:
        return {'message': 'The Blockchain is not valid.'}


# GET THE PENDING TRANSACTIONS

@app.get('/pending_transactions')
def pending_transactions():
    return {'pending_transactions': blockchain.transactions}


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


# GET USER BY ID
@app.get("/get_user/{user_id}")
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    async with db.begin():  # Begin transaction for async DB operations
        # Query user by email asynchronously
        result = await db.execute(select(User).filter(user_id == User.id))
        user = result.scalars().first()

        # Check if user exists
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

    return [user.email, user.password]


# SET A POSITION TO A USER
@app.put("/add_position/{id}")
async def add_position(
        id: int,
        latitude: float,
        longitude: float,
        session: AsyncSession = Depends(get_async_session)
):
    # Query the user
    query = await session.execute(select(User).where(id == User.id))
    user = query.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Create a Point object and convert it to WKTElement
    position = WKTElement(f"POINT({longitude} {latitude})", srid=4326)

    # Update user's position
    user.current_position = position
    session.add(user)
    await session.commit()

    return {"message": "User position updated successfully", "id": user.id}




# GET REWARDED ENDPOINT

# CHECK IF A USER IS NEAR TO ANY CAMP
# IF THE USER IS NEAR A CAMP THEY WILL GET REWARDED (MAKE A TRANSACTION FROM THE CAMP'S BALANCE TO THE USER'S BALANCE
@app.get('/reward_me')
async def reward_me(email: str, session: AsyncSession = Depends(get_async_session)):
    try:
        async with session.begin():  # Begin transaction for async DB operations
            # Query user by email asynchronously
            result = await session.execute(select(User).filter(User.email == email))
            user = result.scalars().first()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Ensure user's current position is set
            if not user.current_position:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User's current position is not set"
                )

            # Check if there is a camp within a 10-meter radius
            near_camp_query = await session.execute(
                select(Camp)
                .filter(
                    ST_DWithin(
                        Camp.geo_location,
                        ST_SetSRID(user.current_position, 4326),
                        10
                    )
                )
            )
            camp = near_camp_query.scalar_one_or_none()
            print(camp)

            # If no camp is found, return an error
            if not camp:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="There is no camp near this user"
                )

            # Perform the transaction: transfer 10 points from camp to user
            index = blockchain.add_transaction(
                sender=camp.camp_name,
                receiver=user.email,
                amount=10
            )

            response = {'message': f'Transaction added to block {index}'}

    except HTTPException as http_exc:
        # Rethrow HTTPExceptions to keep their status code and details
        raise http_exc
    except Exception as e:
        # Log unexpected exceptions for debugging
        print(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Something went wrong"
        )

    return response

# MINE A BLOCK

@app.get('/mine_block')
def mine_block():
    # Check if the blockchain is valid before mining a new block
    if not blockchain.is_chain_valid():
        raise HTTPException(status_code=400, detail="Blockchain is not valid")

    # Get the previous block to determine the previous hash
    previous_block = blockchain.get_previous_block()
    previous_hash = previous_block['hash']

    # Aggregate balances from the previous block and the current block
    balances = {k: blockchain.balances.get(k, 0) + previous_block['balances'].get(k, 0) for k in
                set(blockchain.balances) | set(previous_block['balances'])}
    # Create a new block with the aggregated balances and previous hash
    block = blockchain.create_block(balances, previous_hash)

    is_block_valid = True
    sender_aggregations = {}
    receiver_aggregations = {}
    for transaction in block['transactions']:
        sender = transaction["sender"]
        receiver = transaction["receiver"]
        amount = transaction["amount"]

        if sender in sender_aggregations:
            sender_aggregations[sender] += amount
        else:
            sender_aggregations[sender] = amount

        if receiver in receiver_aggregations:
            receiver_aggregations[receiver] += amount
        else:
            receiver_aggregations[receiver] = amount

    if not block['balances'] and sender_aggregations:
        is_block_valid = False
        raise HTTPException(status_code=400, detail="Invalid transaction data: Not enough amount")

    if block['balances']:
        for sender in sender_aggregations:
            sender_balance = block['balances'].get(sender, 0)
            if sender_balance < sender_aggregations[sender]:
                is_block_valid = False
                raise HTTPException(status_code=400, detail=f"Invalid transaction data for {sender}: Not enough amount")
            else:
                block['balances'][sender] = sender_balance - sender_aggregations[sender]

        for receiver in receiver_aggregations:
            receiver_balance = block['balances'].get(receiver, 0)
            block['balances'][receiver] = receiver_balance + receiver_aggregations[receiver]

    if is_block_valid:
        # Append the mined block to the blockchain and update the peer copy
        blockchain.chain.append(block)
        blockchain.peer_b = copy.deepcopy(blockchain.chain)

    response = {'message': 'A block is MINED',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'nonce': block['nonce'],
                'previous_hash': block['previous_hash'],
                'hash': block['hash'],
                'balances': block['balances'],
                'transactions': block['transactions']}

    return response
