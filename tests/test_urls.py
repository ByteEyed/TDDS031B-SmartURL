def test_create_url_generated_code(client, auth_headers):
    """Test shortening a long URL with auto-generated short code."""
    payload = {
        "original_url": "https://www.example.com/articles/python/fastapi/tutorial"
    }
    response = client.post("/api/v1/urls", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == payload["original_url"]
    assert len(data["short_code"]) == 6
    assert data["is_active"] is True
    assert data["click_count"] == 0


def test_create_url_custom_alias(client, auth_headers):
    """Test shortening a URL with valid custom alias."""
    payload = {
        "original_url": "https://fastapi.tiangolo.com",
        "custom_alias": "fastapi-docs"
    }
    response = client.post("/api/v1/urls", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["short_code"] == "fastapi-docs"


def test_create_url_duplicate_alias(client, auth_headers):
    """Test 409 conflict when custom alias is already in use."""
    payload = {
        "original_url": "https://example.com/1",
        "custom_alias": "my-alias"
    }
    res1 = client.post("/api/v1/urls", json=payload, headers=auth_headers)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/urls", json=payload, headers=auth_headers)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "Custom alias is already in use"


def test_create_url_invalid_alias_format(client, auth_headers):
    """Test Pydantic validation rejection for custom alias containing invalid characters."""
    payload = {
        "original_url": "https://example.com",
        "custom_alias": "invalid alias!"
    }
    response = client.post("/api/v1/urls", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_create_url_invalid_scheme(client, auth_headers):
    """Test Pydantic validation rejection for invalid URL scheme (e.g. ftp://)."""
    payload = {
        "original_url": "ftp://files.example.com/download"
    }
    response = client.post("/api/v1/urls", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_create_url_unauthenticated(client):
    """Test unauthenticated request rejection (401 Unauthorized)."""
    payload = {
        "original_url": "https://example.com"
    }
    response = client.post("/api/v1/urls", json=payload)
    assert response.status_code == 401


def test_list_user_urls(client, auth_headers):
    """Test retrieving user's paginated list of URLs."""
    client.post("/api/v1/urls", json={"original_url": "https://example.com/1"}, headers=auth_headers)
    client.post("/api/v1/urls", json={"original_url": "https://example.com/2"}, headers=auth_headers)

    response = client.get("/api/v1/urls?page=1&limit=10", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["urls"]) == 2


def test_get_url_detail_owner(client, auth_headers):
    """Test owner retrieving detail of their short URL."""
    create_res = client.post(
        "/api/v1/urls",
        json={"original_url": "https://python.org", "custom_alias": "pyorg"},
        headers=auth_headers
    )
    code = create_res.json()["short_code"]

    response = client.get(f"/api/v1/urls/{code}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["short_code"] == "pyorg"


def test_get_url_detail_forbidden_for_non_owner(client, auth_headers, second_auth_headers):
    """Test 403 Forbidden when user attempts to access another user's URL management endpoint."""
    create_res = client.post(
        "/api/v1/urls",
        json={"original_url": "https://private.org"},
        headers=auth_headers
    )
    code = create_res.json()["short_code"]

    # User 2 attempts to fetch details of User 1's URL
    response = client.get(f"/api/v1/urls/{code}", headers=second_auth_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Access forbidden: You do not own this URL"


def test_update_url_owner(client, auth_headers):
    """Test owner modifying is_active state of URL."""
    create_res = client.post(
        "/api/v1/urls",
        json={"original_url": "https://toggle.com"},
        headers=auth_headers
    )
    code = create_res.json()["short_code"]

    patch_res = client.patch(
        f"/api/v1/urls/{code}",
        json={"is_active": False},
        headers=auth_headers
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_active"] is False


def test_delete_url_owner(client, auth_headers):
    """Test owner deleting a short URL."""
    create_res = client.post(
        "/api/v1/urls",
        json={"original_url": "https://todelete.com"},
        headers=auth_headers
    )
    code = create_res.json()["short_code"]

    del_res = client.delete(f"/api/v1/urls/{code}", headers=auth_headers)
    assert del_res.status_code == 204

    # Verify deleted
    get_res = client.get(f"/api/v1/urls/{code}", headers=auth_headers)
    assert get_res.status_code == 404
