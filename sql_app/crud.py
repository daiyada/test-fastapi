from typing import List

from sqlalchemy.orm import Session

from . import models, schemas


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def get_active_users(db: Session):
    return db.query(models.User).filter(models.User.is_active == True).all()


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


def delete_user(db: Session, user_for_deletion: models.User, active_users: List[models.User]):
    if active_users == 1:
        user_for_deletion.is_active = False
    else:
        user_for_deletion.is_active = False
        min_user_id = min(active_users, key=lambda x:x.user_id)
        if user_for_deletion.items:
            for item in user_for_deletion.items:
                item.owner_id = min_user_id
    return user_for_deletion