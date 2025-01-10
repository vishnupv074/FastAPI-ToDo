from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.models import Users
from passlib.context import CryptContext
from app.database import SessionLocal
from sqlalchemy.orm.session import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm


router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependancy injection
db_dependancy = Annotated[Session, Depends(get_db)]


def authenticate_user(username, password, db) -> bool:
    user = db.query(Users).filter(Users.username == username).first()
    if not user:
        return None
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    return user


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "vishnupv",
                "email": "vishnu@gmail.com",
                "first_name": "Vishnu",
                "last_name": "P V",
                "password": "pass123",
                "role": "admin",
            }
        }
    }


@router.post("/auth", status_code=status.HTTP_201_CREATED)
async def create_user(
    db: db_dependancy, create_user_request: CreateUserRequest
):
    # create_user_model = Users(**create_user_request.model_dump())
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        role=create_user_request.role,
        hashed_password=bcrypt_context.hash(create_user_request.password),
        is_active=True,
    )

    db.add(create_user_model)
    db.commit()


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependancy,
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return "User not authenticated!"
    return "Successful Authentication"
