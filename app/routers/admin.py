from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Path, status
from app.models import Todos
from app.database import SessionLocal
from .auth import get_current_user


router = APIRouter(prefix="/admin", tags=["admin"])
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


@router.get("/todo", status_code=status.HTTP_200_OK)
async def read_all(user: user_dependancy, db: db_dependancy):
    """
    Fetches all todos from the database.

    Args:
        user: Authenticated user dependency.
        db: Database session dependency.

    Returns:
        List of all todo items.

    Raises:
        HTTPException: If user authentication fails or user role is not
                       'admin'.
    """
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication Failed!")
    return db.query(Todos).all()


@router.delete("/todos/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependancy, db: db_dependancy, todo_id: int = Path(gt=0)
):
    """
    Deletes a todo item by its ID.

    Args:
        user: Authenticated user dependency.
        db: Database session dependency.
        todo_id (int): The ID of the todo item to be deleted, must be greater
                       than 0.

    Raises:
        HTTPException: If user authentication fails or user role is not 'admin'
        HTTPException: If the todo item is not found.

    Returns:
        None.
    """
    if user is None or user.get("user_role") != "admin":
        raise HTTPException(status_code=401, detail="Authentication Failed!")

    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found!"
        )
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
