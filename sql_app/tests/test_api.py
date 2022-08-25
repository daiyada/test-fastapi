

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

    response2 = client.post(
        "/token",
        json=user_info
    )
    # assert response2.status_code == 200, response.text
    # data2 = response2.json()
    # assert data2.get("access_token")
    # assert data2.get("token_type") == "bearer"



    # response = client.get(f"/users/{user_id}")
    # assert response.status_code == 200, response.text
    # data = response.json()
    # assert data["email"] == "deadpool@example.com"
    # assert data["id"] == user_id
