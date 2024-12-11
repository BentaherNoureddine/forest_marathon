from fastapi import APIRouter, Depends, HTTPException
from model.User import User
from model.dto.userRequest import UserCreate, GetUser, UserLogin
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from database.database import get_db

router = APIRouter(prefix="/user", tags=["User"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# CRYPT THE PASSWORD
def hash_password(password: str):
    return pwd_context.hash(password)


# CREATE USER ENDPOINT
@router.post("/create", status_code=201)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = User(email=user.email, password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# LOGIN ENDPOINT
@router.get("/login", response_model=GetUser, status_code=200)
def login(request: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    # Check if user exists and password is valid
    if not user:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

    try:
        if not pwd_context.verify(request.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid Credentials")
    except ValueError as e:
        # This exception is thrown when the bcrypt hash is invalid
        raise HTTPException(status_code=500, detail=f"Error verifying password: {str(e)}")

    # Return user data if authentication is successful
    return user
