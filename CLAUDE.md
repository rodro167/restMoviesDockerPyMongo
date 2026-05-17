# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Flask REST API for movies backed by MongoDB, with JWT authentication, Docker containerization, and Terraform IaC for GCP deployment.

## Running the Project

**Full stack (Docker Compose):**
```bash
docker-compose up -d
# API available at http://localhost:4000
```

**Local development (Python only, requires a running MongoDB):**
```bash
pip install -r requirements.txt
cp .env.example .env   # then edit with real values
python setup_db.py     # initialize collections and indexes (idempotent)
python mongoRestMovies.py
```

**Initialize/seed the database:**
```bash
python setup_db.py
```

## Testing

**Smoke tests (integration):**
```bash
python smoke_test.py                                     # local
BASE_URL=http://<host>:4000 python smoke_test.py         # remote
```

The smoke test covers all endpoints including auth, movie CRUD, ratings, comments, and error cases. There is no unit test suite — `smoke_test.py` is the primary QA tool.

**Performance tests:**
Use the JMeter suite at `Performance/RestMoviesPerformance.jmx` with `Performance/populateUsers.csv` as the data source.

## Docker Build & Publish

```bash
./build_and_push.sh [VERSION]   # builds + pushes rodro167/restmovies:latest (and optionally a versioned tag)
```

## GCP Deployment (Terraform)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars   # fill in values
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply
```

The startup script (`startup.sh.tpl`) installs Docker, pulls the image, generates `.env` and `docker-compose.yaml`, starts the services, and runs `setup_db.py` automatically.

## Architecture

### Entry Point & Routing (`mongoRestMovies.py`)

Single Flask app file that owns:
- App initialization, JWT config, MongoDB connection pool
- All route definitions (blueprints are not used — routes live directly here)
- Global error handlers (400, 404, 500)
- All protected routes use `@jwt_required()`

### Module Responsibilities

| File | Purpose |
|---|---|
| `mongoRestMovies.py` | App factory, routes, error handlers |
| `restMoviesGuest.py` | Query + write logic for movies, ratings, comments |
| `restMoviesAdmin.py` | `login()` and credential validation (scrypt via Werkzeug) |
| `db_helpers.py` | `query_movies()`, `parse_object_id()`, `require_json()` |
| `setup_db.py` | Creates collections + indexes, seeds one sample movie |
| `smoke_test.py` | Integration test runner |
| `terraform/main.tf` | Provisions GCP VM, firewall rules, and external IP |
| `terraform/variables.tf` | Input variables (project_id, region, machine_type, etc.) |
| `terraform/outputs.tf` | Outputs after apply (VM external IP, SSH command) |
| `terraform/startup.sh.tpl` | VM bootstrap: installs Docker, pulls image, generates `.env` and `docker-compose.yaml`, runs `setup_db.py` |
| `Performance/RestMoviesPerformance.jmx` | JMeter load test plan |
| `Performance/populateUsers.csv` | Synthetic users (username, password) consumed by the JMX `CSV Data Set Config` |


### Database Collections

- **movies** — `title`, `year`, `runtime`, `genres[]`, `directors[]`, `cast[]`, `countries[]`, `plot`. Indexed on each array/scalar field.
- **users** — `username` (unique), `password` (scrypt hash).
- **ratings** — `movieId`, `userId`, `stars` (1–10). Unique index on `(movieId, userId)`; rating is upserted, not duplicated.
- **comments** — `movieId`, `userId`, `comment`, `createdAt`. Indexed on `(movieId, createdAt)` for sorted retrieval.

MongoDB ObjectIds are validated via `parse_object_id()` and returned as strings in JSON responses.

### Authentication Flow

1. `POST /login` → validates credentials, returns JWT (`Authorization: Bearer <token>`)
2. All routes except `/login` and `/users/register` require the JWT header
3. Token identity = `username`; expiry configurable via `JWT_ACCESS_TOKEN_EXPIRES_HOURS`

### Pagination

Movie list queries support `?page=1&limit=20` (skip-based). Default limit is 20.

## Environment Variables

| Variable | Default | Notes |
|---|---|---|
| `MONGO_URI` | `mongodb://localhost:27017/` | In Compose, use `mongodb://mongo:27017/` |
| `MONGO_DB` | `restMovies` | |
| `JWT_SECRET_KEY` | — | Required; no safe default |
| `FLASK_PORT` | `4000` | |
| `JWT_ACCESS_TOKEN_EXPIRES_HOURS` | `24` | |

## Key Conventions

- All responses are JSON with consistent `{"error": "..."}` shape for failures.
- `db_helpers.py` centralizes input validation — use `require_json()` and `parse_object_id()` rather than replicating inline.
- Routes use both canonical (`/movies/<id>`) and legacy (`/movies/update/<id>`) paths for backwards compatibility; keep both when modifying.
- Ratings are upserted (one per user per movie); comments always append.

## Roadmap / Work in Progress

This repo is being refactored. Upcoming changes (not yet implemented):

1. **Directory restructuring** — move source code under `api/`, infra under `infra/`,
   tests under `load-tests/`. Current flat layout is the v0.1 snapshot.
2. **Monitoring stack** — add Prometheus + Grafana + cAdvisor + node-exporter
   to `docker-compose.yaml`. Instrument `mongoRestMovies.py` with `prometheus_client`
   to expose `/metrics` (RPS, latency per endpoint, error rate).
3. **GCP firewall rule** — open port 3000 (Grafana) restricted to operator IP.
4. **Static external IP** — replace dynamic IP in Terraform.

When working on monitoring, the SUT (API + Mongo) and the observability stack
share the same VM for simplicity. JMeter runs from the developer's local machine.

## Operational Notes

- The Docker image `rodro167/restmovies:latest` is public on Docker Hub and is
  the source of truth for VM deployments. Local code changes require running
  `build_and_push.sh` before `terraform apply` picks them up.
- MongoDB data is **not** persisted to a Docker volume in the current compose
  setup — restarting the container loses data. This is intentional for the
  training context but must be revisited before any real use.
- `setup_db.py` is idempotent and safe to run multiple times.
- Smoke test creates `smoke_test_user` but does not clean it up afterwards.