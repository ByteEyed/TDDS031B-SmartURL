def test_register_user_success(client):
    """Test successful user registration."""
    payload = {
        "username": "newstudent",
        "email": "student@university.edu",
        "password": "SecurePassword123"
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newstudent"
    assert data["email"] == "student@university.edu"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


def test_register_duplicate_username(client):
    """Test registration failure with duplicate username."""
    payload = {
        "username": "duplicateman",
        "email": "first@example.com",
        "password": "Password123"
    }
    response1 = client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    payload_dup = {
        "username": "duplicateman",
        "email": "second@example.com",
        "password": "Password123"
    }
    response2 = client.post("/api/v1/auth/register", json=payload_dup)
    assert response2.status_code == 409
    assert response2.json()["detail"] == "Username is already registered"


def test_register_duplicate_email(client):
    """Test registration failure with duplicate email."""
    payload1 = {
        "username": "userone",
        "email": "same@example.com",
        "password": "Password123"
    }
    client.post("/api/v1/auth/register", json=payload1)

    payload2 = {
        "username": "usertwo",
        "email": "same@example.com",
        "password": "Password123"
    }
    response = client.post("/api/v1/auth/register", json=payload2)
    assert response.status_code == 409
    assert response.json()["detail"] == "Email address is already registered"


def test_login_success(client):
    """Test successful OAuth2 password login and JWT retrieval."""
    reg_payload = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "SecretPassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_data = {
        "username": "loginuser",
        "password": "SecretPassword123"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_password(client):
    """Test login failure with invalid password."""
    reg_payload = {
        "username": "loginuser2",
        "email": "login2@example.com",
        "password": "SecretPassword123"
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_data = {
        "username": "loginuser2",
        "password": "WrongPassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"
