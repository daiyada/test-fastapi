from datetime import timedelta
from os import access

from jose import jwt
from jose.exceptions import JWTError
from pydantic import ValidationError
import pytest

from ..auth import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token
)
from ..crud import get_user_by_email

class TestUserCreation(object):
    def test_create_user(self, client, test_db):
        response = client.post(
            "/users/",
            json={
                "email": "deadpool@example.com",
                "password": "chimichangas4life"
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "deadpool@example.com"
        assert "id" in data
        user_id = data["id"]

        response = client.get(f"/users/{user_id}")
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["email"] == "deadpool@example.com"
        assert data["id"] == user_id

############################################
# 問題1に関するテスト
############################################

class TestAuthTokenCreation(object):
    """
    @relation 問題1
    @brief 認証トークン発行に関するテスト
    """

    def test_create_auth_token_successfully(self, test_db, client, test_user):
        """
        @brief  [正常系] トークンを作成して、そのトークンをデコードして
                登録したユーザー情報が確認できるか
        """
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": test_user.email}, expires_delta=expires
        )
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        authenticated_user = get_user_by_email(test_db, email=email)
        assert authenticated_user.email == test_user.email
        assert authenticated_user.id == test_user.id

    @pytest.mark.parametrize(
        "secret_key, error", (
            ("wrong key", JWTError),
            (b"byte-formatted wrong key", JWTError)
        )
    )
    def test_invalid_token(self, client, test_user, secret_key, error):
        """
        @brief  [異常系] エンコードとデコードでSecret keyが異なる場合
        """
        expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        with pytest.raises(error):
            access_token = create_access_token(
                data={"sub": test_user.email}, expires_delta=expires
            )
            jwt.decode(access_token, secret_key, algorithms=[ALGORITHM])


class TestUserAunthentication(object):
    """
    @relation 問題1
    @brief ユーザー認証に関するテスト
    """

    def test_authenticate_user_normally(self, test_db, client, test_user):
        """
        @brief  [正常系] DBに登録済みのユーザーにログインして情報にアクセス
                できるか
        """
        entry_data = {
                "email": test_user.email,
                "password": "chimichangas4life"
            }
        response = client.post(
            "/token",
            json=entry_data
        )
        assert response.status_code == 200, response.text
        assert response.json().get("access_token")
        assert response.json().get("token_type") == "bearer"
        access_token = response.json().get("access_token")
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        authenticated_user = get_user_by_email(test_db, email=email)
        assert authenticated_user.email == test_user.email
        assert authenticated_user.id == test_user.id


    @pytest.mark.parametrize(
        "email, password, status_code",
        (
            ("deadpool@example.com", "aaa", 401),
            ("deadpool@example.com", None, 422),
            ("wrong", "chimichangas4life", 401),
            (None, "chimichangas4life", 422)
        )
    )
    def test_authentication_with_wrong_entry_data(self, test_db, client, test_user, email, password, status_code):
        """
        @brief  [異常系] エントリー情報が異なる場合
        """
        entry_data = {
                "email": email,
                "password": password
            }
        response = client.post(
            "/token",
            json=entry_data
        )
        assert response.status_code == status_code
        assert "access_token" not in response.json()
        assert "token_type" not in response.json()