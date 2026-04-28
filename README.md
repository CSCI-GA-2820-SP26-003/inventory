# Inventory Service

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)
[![CI Build](https://github.com/CSCI-GA-2820-SP26-003/inventory/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-SP26-003/inventory/actions)
[![codecov](https://codecov.io/gh/CSCI-GA-2820-SP26-003/inventory/branch/master/graph/badge.svg)](https://codecov.io/gh/CSCI-GA-2820-SP26-003/inventory)

The Inventory service is a RESTful API that tracks product stock levels and conditions for an e-commerce application. It is part of the NYU DevOps course project.

## Setup

### Prerequisites

- [Docker](https://www.docker.com/)
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

### Getting Started

1. Clone the repository and open it in VS Code.
2. When prompted, click **Reopen in Container** (or run the `Dev Containers: Reopen in Container` command). This starts a development container with Python, PostgreSQL, and all dependencies pre-installed.
3. Initialize the database and optionally seed it with sample data:

```bash
flask db-create
flask seed-db
```

4. Start the service:

```bash
make run
```

The service will be available at `http://localhost:8080`.

Interactive API documentation (Swagger UI) is at `http://localhost:8080/apidocs`.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URI` | PostgreSQL connection string | set via `postgres-creds` secret in k8s |
| `FLASK_RUN_PORT` | Port the Flask dev server listens on | `8080` |

Copy `dot-env-example` to `.env` to set `FLASK_APP` locally if needed.

## Running Tests

### Unit Tests

```bash
make test
```

Runs the full test suite with `pytest` and enforces a minimum coverage threshold of 95%.

### Linting

```bash
make lint
```

Runs `flake8` and `pylint` against `service/` and `tests/`.

### BDD / Integration Tests

```bash
make bdd
```

Runs the Behave feature suite against a running instance of the service. The service must already be started (`make run`) before running BDD tests locally. In CI and in the Tekton pipeline these run against the deployed service.

## Continuous Integration

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push and pull request to `master`. It:

1. Starts a PostgreSQL 15 service container
2. Installs Python dependencies via `pipenv`
3. Starts the service and checks `/api/health`
4. Runs `flake8` and `pylint`
5. Runs `pytest` with coverage reporting to Codecov
6. Runs the Behave BDD suite with a headless Chrome driver

## Deployment

### OpenShift / Tekton CD Pipeline

The production deployment runs on OpenShift via a Tekton `inventory-cd-pipeline`. The pipeline performs:

1. **git-clone** — checks out the repository
2. **lint** — runs `pylint` against `service/`
3. **test** — runs `pytest` (lint and test run in parallel)
4. **buildah** — builds and pushes the container image to the OpenShift internal registry
5. **deploy** — applies k8s manifests and rolls out the new image
6. **bdd** — runs Behave tests against the live deployment URL

#### Automatic Deploys (Webhook)

Merging to `master` triggers a webhook that fires the `cd-listener` EventListener, which starts a pipeline run automatically via the Tekton trigger template.

#### Manual Deploy

Use `scripts/deploy.sh` to apply all manifests and trigger the pipeline manually:

```bash
bash scripts/deploy.sh
```

The script will:

- Verify `oc` and `tkn` CLIs are installed
- Check that you are logged in to OpenShift (exits with an error if not — run `oc login <cluster-url>` first)
- Print the current OpenShift user and project
- Apply PostgreSQL manifests (`k8s/postgres/`)
- Apply Tekton manifests (workspace, tasks, pipeline, event listener)
- Apply the application Route (`k8s/route.yaml`)
- Wait up to 120 s for PostgreSQL to be ready
- Prompt for a branch or commit SHA to deploy (press **Enter** to use the default: `master`)
- Start the pipeline and stream logs live
- Print a pipeline run summary on completion

**Prerequisites:** you must be logged in to the OpenShift cluster before running the script.

```bash
oc login <cluster-url>
oc project <your-namespace>
bash scripts/deploy.sh
```

### Local Kubernetes (K3D)

To deploy on a local K3D cluster:

```bash
make cluster      # create a K3D cluster with a local registry
make deploy       # apply k8s/ manifests with kubectl
```

## API Reference

The service mounts all REST endpoints under the `/api` prefix. Interactive docs are at `/apidocs`.

### Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/` | Serves the Selenium/UI testing front end |
| `GET` | `/api/health` | Health check (used by k8s readiness probe) |
| `GET` | `/api/inventory` | List all inventory items (supports filters) |
| `GET` | `/api/inventory/<public_id>` | Retrieve a single inventory item |
| `POST` | `/api/inventory` | Create a new inventory item |
| `PUT` | `/api/inventory/<public_id>` | Update an existing inventory item |
| `DELETE` | `/api/inventory/<public_id>` | Delete an inventory item |
| `POST` | `/api/inventory/<public_id>/restock` | Restock an item by its `restock_amount` |
| `POST` | `/api/inventory/<public_id>/decrement` | Decrement the quantity of an item |

### Query Parameters — `GET /api/inventory`

| Parameter | Type | Description |
|-----------|------|-------------|
| `product_id` | string | Filter by product ID |
| `condition` | string | Filter by condition (`NEW`, `OPEN_BOX`, `USED`) |
| `restock` | boolean | `true` returns only items where `quantity <= restock_level` |

### Create an Inventory Item

**`POST /api/inventory`**

Request body (`application/json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | string | yes | Product identifier (must not be empty) |
| `condition` | string | yes | One of: `NEW`, `OPEN_BOX`, `USED` |
| `quantity` | integer | no | Stock count (default: `0`, must be `>= 0`) |
| `restock_level` | integer | yes | Quantity threshold that triggers a restock |
| `restock_amount` | integer | yes | Number of units to add when restocking |

Example:

```json
{
  "product_id": "PROD-001",
  "quantity": 50,
  "restock_level": 10,
  "restock_amount": 25,
  "condition": "NEW"
}
```

Returns `201 Created` with the created item (including its `public_id` UUID). Returns `409 Conflict` if an item with the same `product_id` and `condition` already exists.

### Update an Inventory Item

**`PUT /api/inventory/<public_id>`**

Send a JSON body with any fields from the create payload. All fields are accepted.

Returns `200 OK` with the updated item, or `404 Not Found`.

### Delete an Inventory Item

**`DELETE /api/inventory/<public_id>`**

Returns `204 No Content`. Idempotent — deleting a non-existent item also returns `204`.

### Restock an Inventory Item

**`POST /api/inventory/<public_id>/restock`**

Increases `quantity` by the item's `restock_amount`. No request body required.

Returns `200 OK` with the updated item, or `404 Not Found`.

### Decrement an Inventory Item

**`POST /api/inventory/<public_id>/decrement`**

Request body (`application/json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `amount` | integer | yes | Number of units to subtract (must be `>= 0` and `<= current quantity`) |

Returns `200 OK` with the updated item. Returns `400 Bad Request` if `amount` exceeds the current quantity.

## Project Structure

```text
.devcontainer/              - VS Code Dev Container configuration
.github/workflows/ci.yml    - GitHub Actions CI pipeline
.tekton/                    - Tekton CD pipeline manifests
  ├── pipeline.yaml         - inventory-cd-pipeline definition
  ├── tasks.yaml            - custom tasks (pylint, pytest-env, deploy, behave)
  ├── workspace.yaml        - PersistentVolumeClaim for the pipeline workspace
  └── events/               - Tekton Triggers (EventListener, TriggerTemplate, etc.)
k8s/                        - Kubernetes / OpenShift manifests
  ├── deployment.yaml       - Deployment for the inventory service
  ├── service.yaml          - ClusterIP Service
  ├── route.yaml            - OpenShift Route (TLS edge termination)
  ├── ingress.yaml          - Kubernetes Ingress
  └── postgres/             - PostgreSQL StatefulSet, Service, PVC, Secret
scripts/
  └── deploy.sh             - Manual deploy script (applies manifests + triggers pipeline)
service/                    - Flask application package
  ├── __init__.py           - application factory
  ├── config.py             - configuration parameters
  ├── models.py             - InventoryItem model and Condition enum
  ├── routes.py             - Flask-RESTX API routes
  └── common/
      ├── cli_commands.py   - Flask CLI commands (db-create, seed-db)
      ├── error_handlers.py - HTTP error handlers
      ├── log_handlers.py   - logging setup
      └── status.py         - HTTP status constants
features/                   - Behave BDD tests
  ├── inventory.feature     - Gherkin feature file
  ├── environment.py        - Behave environment hooks
  └── steps/               - step definitions
tests/                      - pytest unit tests
  ├── factories.py          - Factory Boy model factories
  ├── test_cli_commands.py  - CLI command tests
  ├── test_models.py        - model tests
  └── test_routes.py        - route/API tests
Pipfile                     - Python dependencies (managed with pipenv)
Makefile                    - developer task runner
Procfile                    - honcho process file (used by `make run`)
setup.cfg                   - pytest and coverage configuration
wsgi.py                     - WSGI entry point
dot-env-example             - example .env file
.flaskenv                   - Flask environment defaults (FLASK_RUN_PORT=8080)
.gitignore                  - ignored files
.gitattributes              - line-ending normalization
```

## License

Copyright (c) 2016, 2026 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
