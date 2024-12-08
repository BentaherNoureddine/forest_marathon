from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# connect to the db

SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:@localhost/fast_api_school"
# CREATED THE ENGINE TO ESTABLISH A CONNECTION WITH THE MYSQL DB
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# create a session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        #  the yield stops the function
        yield db
    finally:
        db.close()


Base.metadata.create_all(engine)