from datetime import timedelta
from typing import List

from fastapi.testclient import TestClient
from jose import jwt
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.session import close_all_sessions

from ..auth import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token
)
from ..crud import create_user_item, get_user_by_email, create_user
from ..database import Base, get_db
from ..main import app
from ..models import User
from ..schemas import Item, ItemCreate, UserCreate


client = TestClient(app)


@pytest.fixture(scope="function")
def test_db():
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield db

    Base.metadata.drop_all(bind=engine)
    db.rollback()
    close_all_sessions()
    engine.dispose()


@pytest.fixture(scope="function")
def client():
    client = TestClient(app)
    return client


@pytest.fixture(scope="function")
def test_user(test_db) -> User:
    new_user = UserCreate(
        email="deadpool@example.com",
        password="chimichangas4life"
    )
    existed_user = get_user_by_email(test_db, new_user.email)
    if existed_user:
        return existed_user
    return create_user(test_db, new_user)


@pytest.fixture(scope="function")
def authorized_client(client, test_user, test_db) -> User:
    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": test_user.email}, expires_delta=expires
    )
    client.headers = {
        **client.headers,
        "Authorization": f"Bearer {access_token}",
    }
    return client


@pytest.fixture(scope="function")
def test_3users_with_items(test_db) -> List[User]:
    new_user_info_1 = UserCreate(
        email="a1@example.com",
        password="b14life"
    )
    new_user_info_2 = UserCreate(
        email="b2@example.com",
        password="b24life"
    )
    new_user_info_3 = UserCreate(
        email="c3@example.com",
        password="c34life"
    )
    new_user_1 = create_user(test_db, new_user_info_1)
    new_user_2 = create_user(test_db, new_user_info_2)
    new_user_3 = create_user(test_db, new_user_info_3)

    item_1 = ItemCreate(
        title="Test1",
        description="1 Trial for perfection"
    )
    item_2 = ItemCreate(
        title="Test2",
        description="2 Trial for perfection"
    )
    item_3 = ItemCreate(
        title="Test3",
        description="3 Trial for perfection"
    )
    _ = create_user_item(test_db, item_1, user_id=new_user_1.id)
    _ = create_user_item(test_db, item_2, user_id=new_user_2.id)
    _ = create_user_item(test_db, item_3, user_id=new_user_3.id)
    return [new_user_1, new_user_2, new_user_3]


@pytest.fixture(scope="function")
def test_user_with_item(test_db) -> User:
    new_user_info_1 = UserCreate(
        email="deadpool@example.com",
        password="chimichangas4life"
    )
    new_user_1 = create_user(test_db, new_user_info_1)
    item_1 = ItemCreate(
        title="Test1",
        description="1 Trial for perfection"
    )
    _ = create_user_item(test_db, item_1, user_id=new_user_1.id)
    return new_user_1