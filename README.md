# Task Tracker API (Module 1)

A minimal learning-project skeleton for a Task Tracker REST API, built with
Python and FastAPI.

This is **Module 1**: the goal here is only to stand up a working FastAPI
application with a health check endpoint, a clean project layout, and a
test in place — nothing more. The project now includes a lightweight SQLite
+ SQLModel storage layer for local development, while still avoiding CRUD
endpoints, authentication, Docker deployment, or frontend work.

The storage layer that will be added in a later module (SQLite + SQLModel)
is documented ahead of time in [`docs/adr/001-storage-layer.md`](docs/adr/001-storage-layer.md)
so the reasoning is recorded before any database code is written.

## Project Structure

```
task-tracker/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app instance + /health endpoint
│   ├── config.py        # Loads PORT / APP_ENV from .env
│   └── routers/
│       └── __init__.py  # Empty placeholder for future route modules
├── tests/
│   ├── __init__.py
│   └── test_health.py    # Test for the /health endpoint
├── docs/
│   └── adr/
│       └── 001-storage-layer.md
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.10+
- pip

## Why SQLite?

SQLite is the lightest practical database for this project because it needs
no separate server process, no installation of a database engine, and no
network configuration. It stores data in a single local file, which makes it
ideal for a learning project, local development, and small demos.

### Install SQLite

SQLite is often already available on macOS and Linux. On Windows, the
simplest approach is to install the official SQLite tools from the SQLite
website or use Python's built-in sqlite3 support, which is already available
through the standard library.

If you want the standalone CLI tools, download them from:

https://www.sqlite.org/download.html

### Make it work with FastAPI

The project uses SQLModel with a SQLite engine created from a local file,
so FastAPI can work with it without a separate database server. The app
creates the schema automatically on startup and uses a simple engine object
for database operations.

### Docker for later deployments

Docker is not required for local development, but it is useful later when you
want to package the API consistently for deployment. A future step could be
to run the FastAPI app in a container and mount the SQLite file into a
persistent volume so the database survives container restarts.

## Setup

1. Clone or copy this project locally, then move into it:

   ```bash
   cd task-tracker
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate      # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

   If you want to pin the exact versions you actually installed, verify them
   with `pip freeze` and then overwrite the requirements file when you are
   happy with the result:

   ```bash
   pip freeze > requirements.txt
   ```

4. Copy the example environment file and adjust if needed:

   ```bash
   cp .env.example .env
   ```

## Running the App

Start the development server with auto-reload:

```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

## Testing the Health Endpoint

With the server running, in another terminal:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok",
  "timestamp": "2026-07-07T12:34:56.789012+00:00"
}
```

## Running Automated Tests

```bash
pytest
```

This runs the included test suite (currently just a check that `/health`
returns HTTP 200 with the expected JSON shape).

## API Docs (Swagger UI)

FastAPI automatically generates interactive API documentation. With the
server running, open:

```
http://localhost:8000/docs
```

You'll see the `/health` endpoint listed, with the ability to try it
directly from the browser. An alternative ReDoc view is also available at
`http://localhost:8000/redoc`.

## What's Intentionally Not Here Yet

Per the current scope, the following are deliberately excluded and will be
addressed in later modules:

- Task CRUD endpoints (create, read, update, delete)
- Database implementation (SQLite + SQLModel, per ADR-001)
- Authentication / user accounts
- Multi-tenancy
- Docker / containerization
- Cloud deployment
- Frontend files
- Notifications / real-time updates
