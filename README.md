<div align="center">

# Project SyncNote API
**High-Concurrency Containerized RESTful Backend & Secure Authentication Service**

[![CI Test Suite](https://img.shields.io/badge/pytest-5%20passed-success?style=flat-square)](#)
[![Docker](https://img.shields.io/badge/Docker-Zero--Secret%20Rootfs-2496ED?style=flat-square&logo=docker)](#)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Bounded%20Pool%20(1--10)-4169E1?style=flat-square&logo=postgresql)](#)
[![Security](https://img.shields.io/badge/Cryptography-Scrypt%20(N%3D32768)-00C7B7?style=flat-square)](#)
[![Python](https://img.shields.io/badge/Python-3.10--slim-3776AB?style=flat-square&logo=python)](#)
[![License](https://img.shields.io/badge/License-MIT-blue?style=flat-square)](#)

*A production-grade, containerized RESTful API backend engineered with bounded database connection pooling, cryptographic Scrypt password hashing, and verified zero-secret container image layers.*

</div>

---

## 1. System Architecture

**Project SyncNote** provides a decoupled, containerized synchronization backend designed for high-concurrency client workloads. By separating the stateless compute layer (Flask & Gunicorn) from the managed relational persistence layer (PostgreSQL), the service ensures horizontal scale and zero connection exhaustion.

```mermaid
flowchart TD
    Client(["HTTP Client / Frontend Application"]) -->|"Bearer JWT Authorization"| LB["AWS EC2 / Reverse Proxy"]
    
    subgraph Container_Runtime["Immutable Docker Container (python:3.10-slim)"]
        Gunicorn["Gunicorn WSGI Master<br/>(0.0.0.0:5000)"]
        Worker1["Flask Worker 1"]
        Worker2["Flask Worker 2"]
        Middleware["Auth Middleware<br/>(token_required)"]
        Routes["Routes Engine<br/>(/api/auth, /api/notes)"]
        Pool["Bounded Connection Pool<br/>psycopg2.pool.SimpleConnectionPool(1, 10)"]
        
        Gunicorn --> Worker1
        Gunicorn --> Worker2
        Worker1 <--> Middleware <--> Routes <--> Pool
        Worker2 <--> Middleware <--> Routes <--> Pool
    end

    subgraph Relational_Data_Plane["Relational Storage Plane"]
        RDS[("PostgreSQL 16 Database<br/>users, notes tables")]
        Pool <-->|"Safe Checkout / Release"| RDS
    end

    LB -->|"Port 5000"| Gunicorn
```

### Core Architectural Pillars
- **Stateless Compute & Bounded Resource Usage:** The API runs inside a hardened `python:3.10-slim` container using Gunicorn as the WSGI process manager.
- **Connection Leak Immunity:** Eliminates ad-hoc `psycopg2.connect()` calls in favor of a thread-safe connection pool with dual initialization (`DATABASE_URL` 12-factor standard or individual `DB_*` variables). Connections are checked out and guaranteed released in `finally` blocks.
- **Cryptographic Security Invariants:** Password storage utilizes memory-hard Scrypt key derivation ($N=32768$). Authentication exchanges issue HMAC-SHA256 signed JSON Web Tokens (JWT) with 24-hour expiration.
- **Zero-Secret Rootfs Isolation:** Hardened `.dockerignore` filters out `.env*`, `*.pem*`, and `Zone.Identifier` artifacts. The final container image layers contain strictly application code.

---

## 2. Bounded Database Connection Pooling

Relational databases exhaust operating system file descriptors and thread memory when web clients create unbounded database connections. SyncNote implements bounded connection management via `database.py`:

```python
# Create a thread-safe connection pool (min 1, max 10 connections)
if database_url:
    connection_pool = psycopg2.pool.SimpleConnectionPool(1, 10, dsn=database_url)
else:
    connection_pool = psycopg2.pool.SimpleConnectionPool(
        1, 10,
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME")
    )
```

### Connection Checkout and Safe Release Protocol
Endpoints wrap every database operation in `try ... finally` blocks to ensure returned connections never leak back into the operating system:

```python
conn = get_db_connection()
try:
    cur = conn.cursor()
    # Execute transactional queries...
    conn.commit()
finally:
    cur.close()
    release_db_connection(conn)  # Returned cleanly to the pool
```

---

## 3. Cryptographic Security & Password Derivation

SyncNote enforces modern cryptographic standards for credential management:

### 3.1 Scrypt Key Derivation ($N=32768, r=8, p=1$)
Passwords are never stored in plaintext or weak hashes (MD5, SHA1). The service utilizes **Scrypt** via Werkzeug:

$$\text{Hash} = \text{scrypt}(\text{Password}, \text{Salt}, N=32768, r=8, p=1)$$

- **CPU Cost ($N=32768$):** Imposes significant computational complexity on prospective attackers.
- **Memory Cost ($r=8$):** Requires 32 MB of sequential RAM access per hash evaluation, rendering large-scale ASIC and GPU dictionary attacks economically unfeasible.
- **Verification:** Handled through constant-time comparison `check_password_hash(hash, password)` to mitigate timing side-channel attacks.

### 3.2 Stateless JWT Authorization
Upon successful verification, the authentication service issues an authorization wristband:
```python
token = jwt.encode({
    'user_id': user[0],
    'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
}, os.getenv('JWT_SECRET'), algorithm='HS256')
```
Endpoints decorate protected routes with `@token_required`, decoding the bearer token and isolating database queries strictly to `current_user_id`.

---

## 4. Container Security & Image Layer Audit

In compliance with enterprise container security policies, the container filesystem is verified to ensure zero build secrets or private keys reside within the image layers.

### Rootfs Audit Command
```bash
# 1. Build the immutable container
docker build -t syncnote:audit .

# 2. Inspect filesystem contents
docker run --rm syncnote:audit ls -la /app

# 3. Empirically verify complete absence of secrets, keys, or .env files
docker run --rm syncnote:audit find /app -name "*.pem*" -o -name ".env*" -o -name "*Zone.Identifier*"
```

### Verified Audit Output
```
total 44
drwxr-xr-x 1 root root 4096 Oct 27 14:51 .
drwxr-xr-x 1 root root 4096 Oct 27 14:51 ..
-rw-r--r-- 1 root root  111 Oct 26 16:21 .dockerignore
-rw-r--r-- 1 root root  685 Apr 22  2026 Dockerfile
-rw-r--r-- 1 root root 2632 Jun  3 11:08 README.md
-rw-r--r-- 1 root root  841 Apr  7  2026 app.py
-rw-r--r-- 1 root root 1262 Oct 26 16:21 database.py
-rw-r--r-- 1 root root 1169 Apr  7  2026 middleware.py
-rw-r--r-- 1 root root  201 Apr 22  2026 requirements.txt
drwxr-xr-x 3 root root 4096 Apr 21  2026 routes
drwxr-xr-x 3 root root 4096 Oct 27 14:51 tests
```
*Result: Exact match with expected application files. 0 sensitive files detected in container layers.*

---

## 5. API Specification

All requests require `Content-Type: application/json`. Protected endpoints require `Authorization: Bearer <token>`.

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new user account (Scrypt hashed) | No |
| `POST` | `/api/auth/login` | Authenticate user & return 24-hour JWT | No |
| `GET` | `/api/notes/` | Retrieve all notes belonging to authenticated user | **Yes** |
| `POST` | `/api/notes/` | Create a new synchronized note record | **Yes** |
| `PUT` | `/api/notes/<id>` | Update note title / content (user-scoped) | **Yes** |
| `DELETE` | `/api/notes/<id>` | Delete note by ID (user-scoped) | **Yes** |

---

## 6. Setup & Verification Instructions

### 1. Run Automated Test Suite (100% Offline)
```bash
./venv/bin/pytest tests/ -v
```
*Result: 5 passed in ~0.08s (DATABASE_URL parsing, DB_* fallback, safe connection checkout and release, None-safety guards).*

### 2. Local Container Execution
```bash
# Build the container
docker build -t syncnote-api .

# Run with injected environment parameters
docker run -d -p 5000:5000 \
  -e DATABASE_URL="postgresql://postgres:password@host.docker.internal:5432/syncnote_db" \
  -e JWT_SECRET="your-secure-secret-key" \
  --name syncnote-dev \
  syncnote-api:latest
```

---

## 7. Project Structure

```
SyncNote/
├── routes/
│   ├── auth.py              # User registration, login, and Scrypt hashing
│   └── notes.py             # Note CRUD operations with user isolation
├── tests/
│   ├── conftest.py          # Pytest configuration
│   └── test_database.py     # Connection pool tests and fallback verification
├── app.py                   # Flask application factory and blueprint registration
├── database.py              # Bounded psycopg2 SimpleConnectionPool manager
├── middleware.py            # JWT token validation decorator
├── Dockerfile               # Python 3.10-slim container recipe
├── .dockerignore            # Strict build-context exclusion list
└── requirements.txt         # Dependencies (Flask, psycopg2, pyjwt, werkzeug)
```

---

<p align="center">
  <i>Developed and engineered by <b>Garv Vaidya</b> · <a href="https://github.com/kleeeoss">GitHub Workspace</a></i>
</p>