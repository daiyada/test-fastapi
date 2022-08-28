from datetime import timedelta

from fastapi import Depends
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
from ..crud import get_user_by_email, create_user
from ..database import Base, get_db
from ..main import app
from ..models import User
from ..schemas import UserCreate


client = TestClient(app)


@pytest.fixture(scope="class")
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


@pytest.fixture(scope="class")
def client():
    client = TestClient(app)
    return client


@pytest.fixture(scope="class")
def test_user(test_db) -> User:
    new_user = UserCreate(
        email="deadpool@example.com",
        password="chimichangas4life"
    )
    existed_user = get_user_by_email(test_db, new_user.email)
    if existed_user:
        return existed_user
    return create_user(test_db, new_user)


@pytest.fixture(scope="class")
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