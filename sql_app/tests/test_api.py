

def test_create_user(test_db, client):
    """
    @brief 問題1用のテストに改変
    """
    user_info = {"email": "deadpool@example.com", "password": "chimichangas4life"}
    response = client.post(
        "/users/",
        json=user_info,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["email"] == "deadpool@example.com"
    assert "id" in data
    user_info["id"] = data["id"]

    response_authenticated = client.post(
        "/token",
        json=user_info
    )
    assert response_authenticated.status_code == 200, response.text
    token = response_authenticated.json()
    assert token.get("access_token")
    assert token.get("token_type") == "bearer"