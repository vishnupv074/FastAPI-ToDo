from typing import Annotated
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from fastapi import FastAPI, Depends, HTTPException, Path, status
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


# Dependancy injection
db_dependancy = Annotated[Session, Depends(get_db)]


class TodosRequest(BaseModel):
    title: str = Field(min_length=3, max_length=50)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(ge=1, lt=6)
    complete: bool

    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Code something",
                "description": "Code some tutorials and push",
                "priority": 1,
                "complete": False,
            }
        }
    }


@app.get("/")
async def read_all(db: db_dependancy):
    return db.query(Todos).all()


@app.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def read_todo(db: db_dependancy, todo_id: int = Path(gt=0)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found!"
    )


@app.post("/todos", status_code=status.HTTP_201_CREATED)
async def create_todo(db: db_dependancy, todo_request: TodosRequest):
    todo_model = Todos(**todo_request.model_dump())

    db.add(todo_model)
    db.commit()
    db.refresh(todo_model)
    return todo_model


@app.put("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def update_todo(
    db: db_dependancy, todo_request: TodosRequest, todo_id: int = Path(gt=0)
):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found!"
        )
    # todo_model.title = todo_request.title
    # todo_model.description = todo_request.description
    # todo_model.priority = todo_request.priority
    # todo_model.complete = todo_request.complete
    # db.add(todo_model)
    for field, value in todo_request.model_dump().items():
        setattr(todo_model, field, value)
    db.commit()


@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(db: db_dependancy, todo_id: int = Path(gt=1)):
    todo_model = db.query(Todos).filter(Todos.id == todo_id).first()
    if todo_model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found!"
        )
    db.query(Todos).filter(Todos.id == todo_id).delete()
    db.commit()
