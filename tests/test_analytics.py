def test_get_analytics_owner(client, auth_headers):
    """Test retrieving click analytics for a short URL by its owner."""
    client.post(
        "/api/v1/urls",
        json={"original_url": "https://analytics-test.com", "custom_alias": "stat1"},
        headers=auth_headers
    )

    # Perform 2 redirects to populate click events
    client.get("/stat1", headers={"user-agent": "TestBrowser/1.0", "referer": "https://google.com"})
    client.get("/stat1", headers={"user-agent": "TestBrowser/2.0", "referer": "https://bing.com"})

    # Fetch analytics
    response = client.get("/api/v1/analytics/stat1", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["short_code"] == "stat1"
    assert data["total_clicks"] == 2
    assert data["last_clicked_at"] is not None
    assert len(data["recent_clicks"]) == 2
    assert data["recent_clicks"][0]["user_agent"] == "TestBrowser/2.0"
    assert data["recent_clicks"][0]["referrer"] == "https://bing.com"


def test_get_analytics_forbidden_non_owner(client, auth_headers, second_auth_headers):
    """Test 403 Forbidden when a user attempts to view analytics for a URL owned by someone else."""
    client.post(
        "/api/v1/urls",
        json={"original_url": "https://private-analytics.com", "custom_alias": "privstat"},
        headers=auth_headers
    )

    response = client.get("/api/v1/analytics/privstat", headers=second_auth_headers)
    assert response.status_code == 403
    assert response.json()["detail"] == "Access forbidden: You do not own this URL"


def test_get_analytics_nonexistent(client, auth_headers):
    """Test 404 Not Found when attempting to fetch analytics for non-existent short code."""
    response = client.get("/api/v1/analytics/missing999", headers=auth_headers)
    assert response.status_code == 404
    assert response.json()["detail"] == "Short URL not found"
