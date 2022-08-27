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
        @brief  [異常系] エンコードとデコードでSecret keyが異なる場合に
                エラーが生じるか
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
        @brief 正常系のテスト
        """
        entry_data = {
                "email": "deadpool@example.com",
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


class TestUserYourself(object):
    """
    @relation 問題1
    @brief ユーザー認証に関するテスト
    """
    # NOTE: これは問題2の方のテストの気がするが、一応問題1用として実装。

    def test_get_yourself(self, test_db, client, test_user):
        """
        @brief 正常系のテスト
        """
        pass


# def test_create_user(test_db, client):
#     """
#     @brief 問題1用のテストに改変
#     """
#     user_info = {"email": "deadpool@example.com", "password": "chimichangas4life"}
#     response = client.post(
#         "/users/",
#         json=user_info,
#     )
#     assert response.status_code == 200, response.text
#     data = response.json()
#     assert data["email"] == "deadpool@example.com"
#     assert "id" in data
#     # user_info["id"] = data["id"]

#     response_authenticated = client.post(
#         "/token",
#         json=user_info
#     )
#     assert response_authenticated.status_code == 200, response.text
#     token = response_authenticated.json()
#     assert token.get("access_token")
#     assert token.get("token_type") == "bearer"