from fastapi import APIRouter, Depends, HTTPException
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from model.User import User
from model.userRequest import UserCreate, GetUser, UserLogin
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext
from sqlalchemy.future import select
from database.geodb import get_async_session  # Import the async session generator

router = APIRouter(prefix="/user", tags=["User"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# CRYPT THE PASSWORD
def hash_password(password: str):
    return pwd_context.hash(password)


# CREATE USER ENDPOINT (Asynchronous version)
@router.post("/create", status_code=201)
async def create_user(user: UserCreate, db: AsyncSession = Depends(get_async_session)):
    # Check if user already exists to avoid duplicates
    async with db.begin():  # Begin transaction for async DB operations
        existing_user = await db.execute(select(User).filter(User.email == user.email))
        existing_user = existing_user.scalars().first()

        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create new user
        new_user = User(email=user.email, password=hash_password(user.password),
                        current_position=from_shape(Point(0, 0), srid=4326))
        db.add(new_user)
        await db.commit()  # Commit the transaction asynchronously

    await db.refresh(new_user)  # Refresh to get the ID and other fields after the transaction is committed

    return [new_user.email, new_user.password]


# LOGIN ENDPOINT (Asynchronous version)
@router.get("/login", response_model=GetUser, status_code=200)
async def login(request: UserLogin, db: AsyncSession = Depends(get_async_session)):
    async with db.begin():  # Begin transaction for async DB operations
        # Query user by email asynchronously
        result = await db.execute(select(User).filter(request.email == User.email))
        user = result.scalars().first()

        # Check if user exists
        if not user:
            raise HTTPException(status_code=401, detail="Invalid Credentials")

        # Verify the password using bcrypt
        try:
            if not pwd_context.verify(request.password, user.password):
                raise HTTPException(status_code=401, detail="Invalid Credentials")
        except ValueError as e:
            # This exception is thrown when the bcrypt hash is invalid
            raise HTTPException(status_code=500, detail=f"Error verifying password: {str(e)}")

    return user  # Return the user data if authentication is successful
