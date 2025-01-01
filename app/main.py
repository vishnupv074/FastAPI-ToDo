from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends
from .models import Base, Todos
from .database import engine, SessionLocal


app = FastAPI()

Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependancy = Annotated[Session, Depends(get_db)]


@app.get("/")
async def read_all(db: db_dependancy):
    return db.query(Todos).all()
