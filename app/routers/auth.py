from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.models import Users
from passlib.context import CryptContext
from app.database import SessionLocal
from sqlalchemy.orm.session import Session
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError


router = APIRouter(prefix="/auth", tags=["auth"])

SECRET_KEY = "a790b95dcbac742efc25987f91572948567be0ea68e102829619b23d5298c76e"
ALGORITHM = "HS256"

# Configurations for password hashing and OAuth2 password flow.

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
"""
Configures the password hashing algorithm using `CryptContext`.

- `schemes`: Specifies the hashing algorithm to use, in this case,
  "bcrypt".
- `deprecated`: Manages deprecated algorithms; "auto" automatically
  handles deprecation.

Returns:
    CryptContext: An instance of `CryptContext` configured for bcrypt
    hashing.
"""

oauth2_bearer = OAuth2PasswordBearer(tokenUrl="auth/token")
"""
Sets up OAuth2 Password Bearer flow using `OAuth2PasswordBearer`.

- `tokenUrl`: The URL where users can submit their username and password
  to obtain an access token.

Returns:
    OAuth2PasswordBearer: An instance of `OAuth2PasswordBearer` configured
    to handle token-based authentication.
"""


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


def create_access_token(
    username: str, user_id: int, role: str, expiry_delta: timedelta
):
    """
    ഒരു നിശ്ചിത ഉപയോക്താവിന് പ്രത്യേക ഗുണങ്ങളുള്ള ഒരു JSON വെബ് ടോക്കൺ (JWT)
      സൃഷ്ടിക്കുന്നു.

    Args:
        username (str): ഉപയോക്താവിന്റെ username.
        user_id (int): ഉപയോക്താവിന്റെ ഐഡി.
        role (str): ഉപയോക്താവിന് നല്കിയ പദവി.
        expiry_delta (timedelta): ടോക്കൺ കാലഹരണപ്പെടുന്ന സമയപരിധി.

    Returns:
        str: ഉപയോക്താവിന്റെ വിവരങ്ങളും കാലഹരണസമയവും അടങ്ങിയ സംയോജിത JWT.

    ഉദാഹരണം:
        >>> from datetime import timedelta
        >>> create_access_token("johndoe", 42, "admin", timedelta(minutes=30))
        'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...'
    """
    encode = {"sub": username, "id": user_id, "user_role": role}
    expires = datetime.now(timezone.utc) + expiry_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    """
    Decodes a JWT token, extracts the user information, and validates the user.

    Args:
        token (str): The JWT token.

    Returns:
        dict: A dictionary containing username, user_id, and user_role.

    Raises:
        HTTPException: If the token is invalid or the user cannot be validated.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        user_role: str = payload.get("user_role")
        if username is None and user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate user!",
            )

        return {"username": username, "id": user_id, "user_role": user_role}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user!",
        )


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


@router.post("/", status_code=status.HTTP_201_CREATED)
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
    """
    Authenticate the user and provide an access token.

    Args:
        form_data (OAuth2PasswordRequestForm):
            The form data containing the user's credentials.
        db (Session): The database session dependency.

    Returns:
        dict: A dictionary containing the access token and token type.

    Raises:
        HTTPException: If the user cannot be authenticated,
        raises a 401 Unauthorized exception.

    Example:
        >>> from fastapi.testclient import TestClient
        >>> client = TestClient(router)
        >>> response = client.post("/token",
            data={"username": "testuser", "password": "testpass"})
        >>> response.json()
        {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ...",
        "token_type": "bearer"}
    """
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate user!",
        )
    token = create_access_token(
        user.username, user.id, user.role, timedelta(minutes=20)
    )
    return {"access_token": token, "token_type": "bearer"}
