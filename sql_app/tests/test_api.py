from datetime import timedelta
import random

from jose import jwt
from jose.exceptions import JWTError
import pytest

from ..auth import (
    SECRET_KEY,
    ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    create_access_token
)
from ..crud import delete_user, get_user_by_email, create_user_item, get_user, get_active_users, delete_user
from ..schemas import ItemCreate
from ..models import User

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
# 問題 1 に関するテスト
############################################


class TestAuthTokenCreation(object):
    """
    @relation 問題 1
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
    @relation 問題 1
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


############################################
# 問題 2 に関するテスト
############################################


class TestGetOwnItems(object):
    """
    @relation 問題 2
    @brief 自身のItemを取得することに関するテスト
    """

    def test_get_own_items(self, test_db, client, authorized_client, test_user):
        """
        @brief  [正常系] 所有しているItemsを取得
        """
        path_param = f"/users/{test_user.id}/items/"

        # 1個目のitemを登録
        new_item = {
            "title": "Test",
            "description": "Trial for perfection"
        }
        response = client.post(
            path_param,
            json=new_item
        )
        item_data = response.json()
        assert response.status_code == 200, response.text
        assert item_data.get("title") == "Test"
        assert item_data.get("description") == "Trial for perfection"
        assert "id" in item_data
        assert "owner_id" in item_data

        # 2個目のitemを登録
        new_item2 = {
            "title": "Test2",
            "description": "Trial for perfection 2"
        }
        response2 = client.post(
            path_param,
            json=new_item2
        )
        assert response2.status_code == 200, response2.text

        response3 = authorized_client.get(
            "/me/items/"
        )
        assert response3.status_code == 200, response3.text


    def test_get_items_under_non_authorization(self, client, test_user):
        """
        @brief  [異常系] ログインしていない状態で自身のItemsを取得できない
                ことを確認
        """
        response = client.get(
            "/me/items/"
        )
        assert response.status_code == 401, response.text


############################################
# 問題 3 に関するテスト
############################################


class TestDeleteUser(object):
    """
    @relation 問題 3
    @brief ユーザー削除に関するテスト
    """
    def test_delete_user_with_active_users(self, test_db, client, test_3users_with_items):
        """
        @brief [正常系] db内に削除対象以外のactive_userが1人以上いる場合の確認
        """
        # リストの頭 ( id = 1 ) のユーザーを消すこととする
        user_for_deletion = test_3users_with_items[0]
        response = client.put(
            f"/users/{user_for_deletion.id}/",
        )
        response_users = response.json()
        assert response.status_code == 200, response.text
        assert response_users[0].get("id") == user_for_deletion.id
        assert response_users[0].get("is_active") == False
        # 削除した際に、残りのactive_userの中で一番小さいidのuserにitemsが移動しているかを確認
        assert response_users[1].get("items")[1].get("title") == user_for_deletion.items[0].title
        assert response_users[1].get("items")[1].get("description") == user_for_deletion.items[0].description


    def test_delete_user_with_non_other_active_users(self, test_db, client, test_user_with_item):
        """
        @brief [正常系] db内に削除対象以外のactive_userが0人の場合の確認
        """
        response = client.put(
            f"/users/{test_user_with_item.id}/",
        )
        response_user = response.json()
        assert response.status_code == 200, response.text
        assert response_user[0].get("is_active") == False


    def test_exist_no_user_for_deletion(self, test_db, client, test_user_with_item):
        """
        @brief [異常系] dbにactive_userがいない場合
        """
        test_user_with_item.is_active = False
        response = client.put(
            f"/users/{test_user_with_item.id}/",
        )
        assert response.status_code == 404, response.text


    def test_exist_no_active_user_in_db(self, test_db, client, test_3users_with_items):
        """
        @brief [異常系] 削除対象のユーザーがdb上にいない場合
        """
        user_1 = test_3users_with_items[0]
        user_1.is_active = False
        response = client.put(
            f"/users/{user_1.id}/",
        )
        assert response.status_code == 404, response.text