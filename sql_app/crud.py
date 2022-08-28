import copy
from typing import List, Union

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_active_users(db: Session):
    return [user for user in db.query(models.User).all() if user.is_active==True]


def create_user(db: Session, user: schemas.UserCreate):
    fake_hashed_password = user.password + "notreallyhashed"
    db_user = models.User(email=user.email, hashed_password=fake_hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_items(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Item).offset(skip).limit(limit).all()


def create_user_item(db: Session, item: schemas.ItemCreate, user_id: int):
    db_item = models.Item(**item.dict(), owner_id=user_id)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item


def delete_user(db: Session, active_users: List[models.User], user_id_for_deletion: int\
                , user_for_deletion: Union[models.User, None] =None):
    for active_user in active_users:
        if active_user.id == user_id_for_deletion:
            user_for_deletion = active_user
    if not user_for_deletion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No user for deletion found.'
            )
    rest_active_users = copy.copy(active_users)
    rest_active_users.remove(user_for_deletion)
    if len(active_users) == 1:
        user_for_deletion.is_active = False
    else:
        user_for_deletion.is_active = False
        min_id_active_user = min(rest_active_users, key=lambda x:x.id)
        for item in user_for_deletion.items:
            item_for_moving = schemas.ItemCreate(title=item.title, description=item.description)
            _ = create_user_item(db, item_for_moving, user_id=min_id_active_user.id)
    return active_users