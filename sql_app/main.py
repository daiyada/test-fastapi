from datetime import timedelta
from secrets import token_urlsafe
from typing import List

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from . import auth, crud, models, schemas
from .database import engine, db_session

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: schemas.UserCreate, db: Session = db_session):
    user = auth.authenticate_user(db, form_data.email, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/health-check")
def health_check(db: Session = db_session):
    return {"status": "ok"}


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = db_session):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = db_session):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users


@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = db_session):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.post("/users/{user_id}/items/", response_model=schemas.Item)
def create_item_for_user(
    user_id: int, item: schemas.ItemCreate, db: Session = db_session
):
    return crud.create_user_item(db=db, item=item, user_id=user_id)


@app.get("/items/", response_model=List[schemas.Item])
def read_items(skip: int = 0, limit: int = 100, db: Session = db_session):
    items = crud.get_items(db, skip=skip, limit=limit)
    return items


@app.get("/me/items/")
async def read_own_items(current_user: schemas.User = Depends(auth.get_current_active_user)):
    return current_user.items


@app.delete("users/{user_id}/")
def delete_user(user_id: int, db: Session = db_session):
    user_for_deletion = crud.get_user(db, user_id)
    active_users = crud.get_active_users(db)
    if not user_for_deletion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No user for deletion found.'
            )
    if not active_users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No active user in db.'
            )
    user = crud.delete_user(db, user_for_deletion, active_users)
    return user.is_active