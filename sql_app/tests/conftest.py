import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.session import close_all_sessions

from ..crud import get_user_by_email, create_user
from ..database import Base
from ..main import app, get_db
from ..models import User
from ..schemas import UserCreate

# SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

# engine = create_engine(
#     SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
# )
# TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# def override_get_db():
#     try:
#         db = TestingSessionLocal()
#         yield db
#     finally:
#         db.close()


# app.dependency_overrides[get_db] = override_get_db

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