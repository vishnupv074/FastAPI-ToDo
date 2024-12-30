from fastapi import FastAPI
from app import models
from .database import engine


app = FastAPI()

models.Base.metadata.create_all(bind=engine)