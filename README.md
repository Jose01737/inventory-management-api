# Inventory Management API

A REST API for managing a small product inventory. FastAPI provides the HTTP endpoints, PostgreSQL stores the records, and Docker Compose runs both services locally.

## Features
- Create, list, view, update, and delete products.
- Validate product names, prices, and quantities.
- Persist data in PostgreSQL.
- Interactive API documentation at `/docs`.

## Requirements
- Docker Desktop or Docker Engine with Compose

## Start
```bash
docker compose up --build
```
Open `http://localhost:8000/docs` to try the endpoints.

## Example product
```json
{
  "name": "USB-C Cable",
  "sku": "CABLE-001",
  "price": 9.99,
  "quantity": 25
}
```

## Stop
```bash
docker compose down
```
To also remove the local database volume, use `docker compose down -v` (this deletes the stored demo data).

## What I learned
REST API design, request validation, relational databases, environment-based configuration, and containerized development.
