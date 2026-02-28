# Inventory Service

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)

The Inventory service is a RESTful API that tracks product stock levels and conditions for an e-commerce application. It is part of the NYU DevOps course project.

## Setup

### Prerequisites

- [Docker](https://www.docker.com/)
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) extension

### Manual Setup

You can also clone this repository and then copy and paste the starter code into your project repo folder on your local computer. Be careful not to copy over your own `README.md` file so be selective in what you copy.

There are 4 hidden files that you will need to copy manually if you use the Mac Finder or Windows Explorer to copy files from this folder into your repo folder.

These should be copied using a bash shell as follows:

```bash
    cp .gitignore  ../<your_repo_folder>/
    cp .flaskenv ../<your_repo_folder>/
    cp .gitattributes ../<your_repo_folder>/
```

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

## Running Tests

```bash
make test
```

This runs the full test suite with `pytest` and enforces a minimum coverage threshold of 95%.

To lint the code:

```bash
make lint
```

## API Reference

All endpoints are under the base path `/inventory`.

### Service Info

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/inventory` | Returns service name, version, and description |

### Inventory Items

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/inventory/items` | List all inventory items (ordered by id) |
| `GET` | `/inventory/items/<public_id>` | Retrieve a single inventory item |
| `POST` | `/inventory/items` | Create a new inventory item |
| `PUT` | `/inventory/items/<public_id>` | Update an existing inventory item |
| `DELETE` | `/inventory/items/<public_id>` | Delete an inventory item |

### Create an Inventory Item

**`POST /inventory/items`**

Request body (`application/json`):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `product_id` | string | yes | Product identifier |
| `quantity` | integer | no | Stock count (default: 0, must be >= 0) |
| `restock_level` | integer | yes | Threshold that triggers a restock |
| `restock_amount` | integer | yes | How many units to reorder |
| `condition` | string | yes | One of: `NEW`, `OPEN_BOX`, `USED` |

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

Returns `201 Created` with the created item. Returns `409 Conflict` if an item with the same `product_id` and `condition` already exists.

### Update an Inventory Item

**`PUT /inventory/items/<public_id>`**

Send a JSON body with the fields to update. All fields from the create payload are accepted.

Returns `200 OK` with the updated item, or `404 Not Found`.

### Delete an Inventory Item

**`DELETE /inventory/items/<public_id>`**

Returns `204 No Content`. This operation is idempotent — deleting a non-existent item still returns 204.

## Project Structure

```text
.gitignore          - this will ignore vagrant and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to fix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
pyproject.toml      - Poetry list of Python libraries required by your code

service/                   - service python package
├── __init__.py            - package initializer
├── config.py              - configuration parameters
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── cli_commands.py    - Flask CLI commands (db-create, seed-db)
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/                     - test cases package
├── __init__.py            - package initializer
├── factories.py           - Factory for testing with fake objects
├── test_cli_commands.py   - test suite for the CLI
├── test_models.py         - test suite for business models
└── test_routes.py         - test suite for service routes
```

## License

Copyright (c) 2016, 2025 [John Rofrano](https://www.linkedin.com/in/JohnRofrano/). All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the New York University (NYU) masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by [John Rofrano](https://cs.nyu.edu/~rofrano/), Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
