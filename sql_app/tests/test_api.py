class TestUserCreation(object):
    def test_create_user(self, test_db, client):
        response = client.post(
            "/users/",
            json={"email": "deadpool@example.com", "password": "chimichangas4life"},
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
        @brief 正常系のテスト
        """
        pass

class TestUserAunthentication(object):
    """
    @relation 問題1
    @brief ユーザー認証に関するテスト
    """

    def test_authenticate_user_successfully(self, test_db, client, test_user):
        """
        @brief 正常系のテスト
        """
        pass

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