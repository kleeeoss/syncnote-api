# SyncNote API 🚀

A production-grade, containerized RESTful backend architecture built for high-performance note synchronization. This project is fully decoupled, containerized using Docker, and deployed on AWS infrastructure utilizing enterprise-level relational storage.

## 🏗️ System Architecture

The application bypasses monolithic constraints by decoupling compute from storage, utilizing an immutable container pattern for seamless deployment scaling.

* **Compute:** AWS EC2 (Ubuntu Server) hosting a detached Docker container runtime.
* **WSGI Server:** Gunicorn serving asynchronous greenlet workers for optimized concurrent connection handling.
* **Database:** AWS RDS running a managed PostgreSQL instance configured with isolated security group firewalls.
* **Container Registry:** Docker Hub for immutable image distribution.

## 🛠️ Tech Stack

* **Backend Framework:** Flask (Python 3.10-slim)
* **Database Engine:** PostgreSQL (Psycopg2)
* **Containerization:** Docker
* **Cloud Platform:** Amazon Web Services (AWS EC2, RDS, VPC, Security Groups)

## ⚡ API Endpoints (Production Sample)

All requests must contain valid JSON headers where applicable.

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | API Health Check / Status | No |
| `POST` | `/api/notes` | Create a new synchronized note | Yes |
| `GET` | `/api/notes` | Retrieve all user notes | Yes |
| `DELETE` | `/api/notes/<id>`| Purge a specific note by ID | Yes |

## 🚀 Local Development Setup

### Prerequisites
* Docker installed locally

### Step-by-Step Execution

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/kleeeoss/syncnote-api.git](https://github.com/kleeeoss/syncnote-api.git)
   cd syncnote-api

2. **Build the localized immutable container:**
    
    ```bash
    docker build -t syncnote-api .
    ```
    
3. **Run the architecture locally (injecting mock environment parameters):**
    
    ```bash
    docker run -d -p 5000:5000 \
      -e DATABASE_URL="postgresql://postgres:your_local_password@localhost:5432/syncnote_local_db" \
      --name syncnote-dev \
      syncnote-api:latest
    ```
    

## ☁️ Cloud Deployment Blueprint

This application is deployed on AWS following industry DevOps paradigms:

* Compiled images are pushed to a central repository (Docker Hub).

    
* An AWS EC2 host pulls the image dynamically.


* Database migrations and continuous connections are maintained securely within an isolated AWS VPC framework via Port Mapping (`5000:5000`).