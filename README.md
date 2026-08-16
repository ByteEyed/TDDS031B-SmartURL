# SMARTURL
### Design and Development of a RESTful URL Shortening API using Python and FastAPI

SMARTURL is an academic RESTful API application developed to demonstrate core concepts of modern Python web development, API architecture, object-relational mapping (ORM), authentication, and database design.

---

## 1. Project Objective

The primary objective of SmartURL is to convert long HTTP/HTTPS URLs into concise, unique short URLs (e.g., `http://localhost:8000/aB92xK`) and safely redirect visitors to original web destinations while tracking access analytics.

---

## 2. Key Features

- **User Authentication**: User registration, login via OAuth2 form-encoded flow, and signed JWT Bearer tokens.
- **URL Shortening**: Automatic 6-character random code generation (using `secrets`) or optional custom alias assignment (e.g., `my-link`).
- **URL Validation**: Pydantic v2 validation ensuring proper HTTP/HTTPS scheme and alias syntax.
- **Collision Prevention**: Database checks preventing duplicate custom short codes or generated collisions.
- **URL Expiration & Deactivation**: Configurable expiration dates (`expires_at`) and manual status toggling (`is_active`).
- **Public Redirect (307)**: HTTP 307 Temporary Redirect with proper HTTP status codes (`404 Not Found` for missing codes, `410 Gone` for expired or inactive links).
- **Click Tracking & Analytics**: Dual-tracking using `click_count` for rapid aggregations and `ClickEvent` logs storing timestamp, IP address, user-agent, and referrer header details.
- **User Ownership Isolation**: Multi-tenant authorization ensuring users can only manage or view analytics for URLs they own.
- **Health Check & Middleware**: Dedicated `/api/v1/health` endpoint pinging SQLite and custom request latency logging middleware.
- **Automated Documentation**: Interactive Swagger UI (`/docs`) and ReDoc (`/redoc`) documentation generated automatically via OpenAPI specifications.

---

## 3. Technology Stack

- **Language**: Python 3.12+ (Tested on Python 3.14)
- **Web Framework**: FastAPI
- **ASGI Server**: Uvicorn
- **Validation & Settings**: Pydantic v2 & `pydantic-settings`
- **Database ORM**: SQLAlchemy 2.x (Modern `Mapped`, `mapped_column`, `select()` syntax)
- **Database Engine**: SQLite 3 (`database.db`)
- **Password Security**: `pwdlib` with Argon2 hashing
- **Token Security**: `PyJWT` (JSON Web Tokens)
- **Test Framework**: `pytest` & FastAPI `TestClient` / `HTTPX`

---

## 4. Architecture & Application Flow

SmartURL follows a clean layered software architecture that separates concerns cleanly across modules:

```
                          +-------------------------+
                          |   Client / Swagger UI   |
                          +-------------------------+
                                       |
                                       v
                          +-------------------------+
                          | RequestLoggingMiddleware|
                          +-------------------------+
                                       |
                                       v
                          +-------------------------+
                          |   FastAPI APIRouters    |
                          | (auth, urls, analytics) |
                          +-------------------------+
                                       |
                   +-------------------+-------------------+
                   |                                       |
                   v                                       v
       +-----------------------+               +-----------------------+
       | Dependencies (get_db, |               |   Pydantic Schemas    |
       |   get_current_user)   |               |     Validation        |
       +-----------------------+               +-----------------------+
                   |
                   v
       +-----------------------+
       |   Services Layer      |
       | (auth, url, analytics)|
       +-----------------------+
                   |
                   v
       +-----------------------+
       |   SQLAlchemy 2.x ORM  |
       +-----------------------+
                   |
                   v
       +-----------------------+
       | SQLite (database.db)  |
       +-----------------------+
```

---

## 5. Folder Structure

```
smarturl/
│
├── app/
│   ├── __init__.py                # Package declaration
│   ├── main.py                    # FastAPI app initialization, lifespan, middleware & routers
│   │
│   ├── core/                      # Application core configuration and security
│   │   ├── __init__.py
│   │   ├── config.py              # Environment configuration using pydantic-settings
│   │   ├── security.py            # Argon2 password hashing & JWT generation/decoding
│   │   └── dependencies.py        # Database session & current user dependencies
│   │
│   ├── database/                  # Database management & SQLAlchemy ORM
│   │   ├── __init__.py
│   │   ├── database.py            # SQLite Engine, SessionLocal & Base model
│   │   └── models.py              # User, URL, ClickEvent SQLAlchemy 2.x models
│   │
│   ├── schemas/                   # Pydantic v2 data models & validators
│   │   ├── __init__.py
│   │   ├── auth.py                # UserRegister, UserResponse, Token, TokenData
│   │   ├── url.py                 # URLCreate, URLUpdate, URLResponse, URLListResponse
│   │   ├── analytics.py           # ClickEventResponse, URLAnalyticsResponse
│   │   └── health.py              # HealthCheckResponse
│   │
│   ├── routers/                   # HTTP Request Routing
│   │   ├── __init__.py
│   │   ├── auth.py                # POST /api/v1/auth/register, POST /api/v1/auth/login
│   │   ├── urls.py                # CRUD /api/v1/urls & GET /{short_code} public redirect
│   │   ├── analytics.py           # GET /api/v1/analytics/{short_code}
│   │   └── health.py              # GET /api/v1/health
│   │
│   ├── services/                  # Core Business Logic Layer
│   │   ├── __init__.py
│   │   ├── auth_service.py        # Registration and credential authentication logic
│   │   ├── url_service.py         # Short code generation, validation & expiration processing
│   │   └── analytics_service.py   # Click event recording & metrics calculation
│   │
│   └── middleware/                # HTTP Middleware
│       ├── __init__.py
│       └── logging.py             # Simple HTTP request logger
│
├── tests/                         # Automated Unit & Integration Tests
│   ├── __init__.py
│   ├── conftest.py                # Isolated SQLite in-memory test database fixtures
│   ├── test_auth.py               # Authentication tests
│   ├── test_urls.py               # URL management tests
│   ├── test_redirect.py           # Public redirect & tracking tests
│   ├── test_analytics.py          # Analytics tests
│   └── test_health.py             # Health check test
│
├── .env                           # Local environment configuration (gitignored)
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git ignore rules
├── requirements.txt               # Project dependencies
└── README.md                      # Academic documentation & viva guide
```

---

## 6. Database Schema

The database consists of three relational tables created using SQLite and managed by SQLAlchemy 2.x ORM models:

### 1. `users` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Autoincrement | Unique user identifier |
| `username` | String(50) | Unique, Indexed, Non-null | Unique username for login |
| `email` | String(100) | Unique, Indexed, Non-null | Unique user email address |
| `hashed_password` | String(255) | Non-null | Argon2 hashed password |
| `created_at` | DateTime | Non-null, Default UTC | Registration timestamp |

*Relationship*: 1 User → Many URLs (`cascade="all, delete-orphan"`)

### 2. `urls` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Autoincrement | Unique URL record identifier |
| `original_url` | Text | Non-null | Full target HTTP/HTTPS URL |
| `short_code` | String(30) | Unique, Indexed, Non-null | Generated or custom short alias |
| `user_id` | Integer | Foreign Key (`users.id`) | Owner user ID |
| `created_at` | DateTime | Non-null, Default UTC | Creation timestamp |
| `expires_at` | DateTime | Nullable | Optional expiration timestamp |
| `is_active` | Boolean | Default `True` | Link activation state |
| `click_count` | Integer | Default `0` | Rapid total click count counter |

*Relationships*: Many URLs → 1 User; 1 URL → Many ClickEvents (`cascade="all, delete-orphan"`)

### 3. `click_events` Table
| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | Integer | Primary Key, Autoincrement | Unique click event identifier |
| `url_id` | Integer | Foreign Key (`urls.id`) | Target short URL ID |
| `timestamp` | DateTime | Non-null, Default UTC | Access timestamp |
| `ip_address` | String(50) | Nullable | Client IP address |
| `user_agent` | String(255) | Nullable | Visitor Browser / Client User-Agent |
| `referrer` | String(255) | Nullable | HTTP Referrer header URL |

*Relationship*: Many ClickEvents → 1 URL

---

## 7. API Endpoints Table

| Method | Endpoint | Description | Auth Required | Status Code |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | System & Database Health Check | No | `200 OK` |
| `POST` | `/api/v1/auth/register` | Register new user account | No | `201 Created` |
| `POST` | `/api/v1/auth/login` | OAuth2 login (returns Bearer token) | No | `200 OK` |
| `POST` | `/api/v1/urls` | Create short URL | Yes (Bearer) | `201 Created` |
| `GET` | `/api/v1/urls` | List authenticated user's URLs | Yes (Bearer) | `200 OK` |
| `GET` | `/api/v1/urls/{short_code}` | Get URL management details | Yes (Bearer) | `200 OK` |
| `PATCH` | `/api/v1/urls/{short_code}` | Update `expires_at` or `is_active` | Yes (Bearer) | `200 OK` |
| `DELETE` | `/api/v1/urls/{short_code}` | Delete short URL | Yes (Bearer) | `204 No Content` |
| `GET` | `/{short_code}` | Public short URL redirect | No | `307 Temporary Redirect` |
| `GET` | `/api/v1/analytics/{short_code}` | Get click analytics details | Yes (Bearer) | `200 OK` |

---

## 8. Installation & Setup Instructions

### Prerequisites
- Python 3.12+ installed on your system.

### Step 1: Clone or Navigate to Project Directory
```bash
cd "d:\user (sarthak)\projects\smarturl"
```

### Step 2: Create and Activate Virtual Environment

**Windows (PowerShell / Command Prompt)**:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

**Linux / macOS**:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Required Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment Configuration
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```

---

## 9. Running the Application

To launch the FastAPI development server with hot-reloading:

```bash
python -m uvicorn app.main:app --reload
```

The application will start at: `http://127.0.0.1:8000`

---

## 10. Interactive API Documentation

FastAPI automatically generates interactive OpenAPI documentation:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

### Authorizing in Swagger UI:
1. Open `http://127.0.0.1:8000/docs`.
2. Register a new user using `POST /api/v1/auth/register`.
3. Click the **Authorize** button at the top right of the Swagger UI.
4. Enter your `username` and `password` into the OAuth2 form modal.
5. Click **Authorize** — all protected endpoints (`/api/v1/urls`, `/api/v1/analytics`) are now unlocked!

---

## 11. Running Automated Tests

The test suite runs against an isolated SQLite in-memory database (`sqlite:///:memory:`) so that tests never pollute or alter the development `database.db`.

Execute pytest using:

```bash
pytest -v
```

---

## 12. Example API Usage (cURL Commands)

### 1. Register User
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{"username": "sarthak", "email": "sarthak@example.com", "password": "StrongPassword123"}'
```

### 2. Login (Get JWT Token)
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=sarthak&password=StrongPassword123"
```

*Response*:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### 3. Create Short URL
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/urls" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>" \
     -H "Content-Type: application/json" \
     -d '{"original_url": "https://www.example.com/articles/python/fastapi/tutorial", "custom_alias": "fastapi-guide"}'
```

### 4. Access Short URL (Redirect)
```bash
curl -i "http://127.0.0.1:8000/fastapi-guide"
```

*Response*:
`HTTP/1.1 307 Temporary Redirect`
`location: https://www.example.com/articles/python/fastapi/tutorial`

### 5. View Analytics
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/analytics/fastapi-guide" \
     -H "Authorization: Bearer <YOUR_ACCESS_TOKEN>"
```

---

## 13. Academic Concepts Demonstrated

This project is specifically designed to demonstrate core concepts taught in an **API Development with Python** curriculum:

1. **REST Architecture Principles**:
   - Resource-based URI hierarchy (`/api/v1/urls`, `/api/v1/analytics`).
   - Stateless server communication using HTTP standard verbs (`GET`, `POST`, `PATCH`, `DELETE`).
   - Semantic HTTP response status codes (`201 Created`, `307 Temporary Redirect`, `401 Unauthorized`, `403 Forbidden`, `404 Not Found`, `409 Conflict`, `410 Gone`, `422 Unprocessable Entity`).

2. **FastAPI & Async Foundations**:
   - `FastAPI` instance management with lifespan hooks for clean database startup.
   - `APIRouter` modularization separating concerns across `auth`, `urls`, `analytics`, and `health`.
   - Automatic OpenAPI schema generation (`/docs` and `/redoc`).

3. **Pydantic v2 Validation & Serialization**:
   - Request body validation (`UserRegister`, `URLCreate`, `URLUpdate`).
   - Custom field validation (`@field_validator`) checking URL protocols (`http://` or `https://`) and custom alias character sets (`a-zA-Z0-9_-`).
   - Response model filtering (`UserResponse` explicitly excluding sensitive password fields).

4. **FastAPI Dependency Injection (`Depends`)**:
   - Database session lifecycle management (`get_db()`) opening and closing SQLite connections per request using `yield`.
   - Security context extraction (`get_current_user()`) decoding JWT tokens and injecting the authenticated user object directly into route parameters.

5. **Modern SQLAlchemy 2.x ORM**:
   - Declarative base modeling (`DeclarativeBase`, `Mapped[...]`, `mapped_column(...)`).
   - Modern query execution using explicit `select()` statements rather than legacy `db.query()`.
   - Relational foreign keys and cascade deletions (`cascade="all, delete-orphan"`).

6. **Authentication & Security Best Practices**:
   - Password hashing using modern **Argon2** via `pwdlib`.
   - Stateless authorization using **PyJWT** (JSON Web Tokens) with expiration metrics.
   - User ownership verification preventing unauthorized access to private management endpoints.

7. **HTTP Middleware**:
   - Asynchronous request logging (`RequestLoggingMiddleware`) logging request path, method, status code, and latency in milliseconds.

8. **Automated Testing**:
   - Unit and integration testing with `pytest` and `TestClient`.
   - Isolated in-memory SQLite database setup using pytest fixtures.

---

## 15. Limitations & Future Improvements

### Current Limitations:
- **Single Instance**: SQLite is a file-based single-file database suited for local execution and academic evaluation, not distributed concurrent writing.
- **Basic Analytics**: Tracks click counts, timestamps, IP addresses, user-agents, and referrers without geographic IP resolution or device parsing.

### Possible Future Improvements:
- **Custom QR Code Generation**: Add an endpoint returning a downloadable QR code image for shortened URLs.
- **Domain Whitelisting**: Allow administrators to restrict allowed destination domains for security filtering.
- **Rate Limiting**: Implement client rate-limiting per IP to protect redirect endpoints from automated abuse.
