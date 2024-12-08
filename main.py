from fastapi import FastAPI
from authentication.authentication import router as register_router
from database.database import engine
from model.User import Base

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
