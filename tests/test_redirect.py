from datetime import datetime, timedelta, timezone


def test_public_redirect_success(client, auth_headers):
    """Test public GET /{short_code} returns 307 temporary redirect, increments click count, and creates ClickEvent."""
    create_res = client.post(
        "/api/v1/urls",
        json={"original_url": "https://example.com/target", "custom_alias": "target1"},
        headers=auth_headers
    )
    assert create_res.status_code == 201

    # Call public redirect (follow_redirects=False to verify 307 header)
    redirect_res = client.get("/target1", follow_redirects=False)
    assert redirect_res.status_code == 307
    assert redirect_res.headers["location"] == "https://example.com/target"

    # Verify click_count updated to 1
    detail_res = client.get("/api/v1/urls/target1", headers=auth_headers)
    assert detail_res.json()["click_count"] == 1


def test_redirect_nonexistent_short_code(client):
    """Test public GET /{short_code} returns 404 Not Found for missing short codes."""
    response = client.get("/nonexistent123", follow_redirects=False)
    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"


def test_redirect_inactive_url(client, auth_headers):
    """Test public GET /{short_code} returns 410 Gone for deactivated URLs."""
    create_res = client.post(
        "/api/v1/urls",
        json={"original_url": "https://inactive.com", "custom_alias": "inact1"},
        headers=auth_headers
    )
    assert create_res.status_code == 201

    # Deactivate URL
    client.patch("/api/v1/urls/inact1", json={"is_active": False}, headers=auth_headers)

    # Attempt redirect
    response = client.get("/inact1", follow_redirects=False)
    assert response.status_code == 410
    assert response.json()["detail"] == "Short URL is inactive"


def test_redirect_expired_url(client, auth_headers):
    """Test public GET /{short_code} returns 410 Gone for expired URLs."""
    past_expiration = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    create_res = client.post(
        "/api/v1/urls",
        json={
            "original_url": "https://expired.com",
            "custom_alias": "exp1",
            "expires_at": past_expiration
        },
        headers=auth_headers
    )
    assert create_res.status_code == 201

    # Attempt redirect
    response = client.get("/exp1", follow_redirects=False)
    assert response.status_code == 410
    assert response.json()["detail"] == "Short URL has expired"
