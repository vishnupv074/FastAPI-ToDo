from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status
from app.models import Users
from app.database import SessionLocal
from .auth import get_current_user, bcrypt_context


router = APIRouter(prefix="/user", tags=["users"])
"""
Initializes an APIRouter instance for admin-related operations.

- `prefix`: Specifies a URL prefix for all endpoints under this router.
  Example: "/admin".
- `tags`: Adds tags to categorize endpoints, here it uses "admin".

Returns:
    APIRouter: An instance of `APIRouter` with the specified prefix
    and tags.
"""


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Dependancy injection
db_dependancy = Annotated[Session, Depends(get_db)]
user_dependancy = Annotated[dict, Depends(get_current_user)]


class UserVerification(BaseModel):
    password: str
    new_password: str = Field(min_length=6)


@router.get("/", status_code=status.HTTP_200_OK)
async def get_user(
    user: Annotated[dict, Depends(get_current_user)], db: db_dependancy
):
    """
    Fetches the user details from the database.

    Args:
        user: Authenticated user dependency.
        db: Database session dependency.

    Raises:
        HTTPException: If user authentication fails.

    Returns:
        User: The authenticated user details from the database.
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed!",
        )

    username = user.get("username")
    user_id = user.get("id")

    if not username or not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user data!",
        )

    user_record = (
        db.query(Users)
        .filter(Users.username == username, Users.id == user_id)
        .first()
    )

    if user_record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found!"
        )

    return user_record


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependancy,
    db: db_dependancy,
    user_verification: UserVerification,
):
    """
    Changes the password for the authenticated user.

    Args:
        user: Authenticated user dependency.
        db: Database session dependency.
        user_verification: UserVerification containing the old and new
                           passwords.

    Raises:
        HTTPException: If authentication or password verification fails.
    """
    # Check if the user is authenticated
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed!",
        )

    # Fetch the authenticated user's record from the database
    user_model = db.query(Users).filter(Users.id == user.get("id")).first()
    if user_model is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed!",
        )

    # Verify the current password provided by the user
    if not bcrypt_context.verify(
        user_verification.password, user_model.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Error in password change!",
        )

    # Hash the new password and update the user's record with it
    user_model.hashed_password = bcrypt_context.hash(
        user_verification.new_password
    )

    # Commit the changes to the database
    db.commit()
