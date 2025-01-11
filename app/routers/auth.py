from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.models import Users
from passlib.context import CryptContext
from app.database import SessionLocal
from sqlalchemy.orm.session import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt


router = APIRouter()

SECRET_KEY = "a790b95dcbac742efc25987f91572948567be0ea68e102829619b23d5298c76e"
ALGORITHM = "HS256"

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


def create_access_token(username: str, user_id: int, expiry_delta: timedelta):

    encode = {"sub": username, "id": user_id}
    expires = datetime.now(timezone.utc) + expiry_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


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


class Token(BaseModel):
    access_token: str
    token_type: str


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


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependancy,
):
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        return "User not authenticated!"
    token = create_access_token(user.username, user.id, timedelta(minutes=20))
    return {"access_token": token, "token_type": "bearer"}
