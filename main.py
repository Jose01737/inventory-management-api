import os
from contextlib import asynccontextmanager

import psycopg
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://inventory_user:local_dev_password@localhost:5432/inventory",
)


def connect():
    return psycopg.connect(DATABASE_URL)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry briefly while PostgreSQL starts in local Docker Compose.
    import time
    last_error = None
    for _ in range(20):
        try:
            with connect() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS products (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        sku TEXT NOT NULL UNIQUE,
                        price NUMERIC(10, 2) NOT NULL CHECK (price >= 0),
                        quantity INTEGER NOT NULL CHECK (quantity >= 0)
                    )
                """)
            last_error = None
            break
        except psycopg.OperationalError as exc:
            last_error = exc
            time.sleep(1)
    if last_error:
        raise last_error
    yield


app = FastAPI(title="Inventory Management API", version="1.0.0", lifespan=lifespan)


class ProductInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    sku: str = Field(min_length=1, max_length=40)
    price: float = Field(ge=0)
    quantity: int = Field(ge=0)


def as_product(row):
    return {
        "id": row[0],
        "name": row[1],
        "sku": row[2],
        "price": float(row[3]),
        "quantity": row[4],
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/products", status_code=201)
def create_product(product: ProductInput):
    try:
        with connect() as conn:
            row = conn.execute(
                "INSERT INTO products (name, sku, price, quantity) VALUES (%s, %s, %s, %s) RETURNING id, name, sku, price, quantity",
                (product.name, product.sku, product.price, product.quantity),
            ).fetchone()
        return as_product(row)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="SKU already exists")


@app.get("/products")
def list_products():
    with connect() as conn:
        rows = conn.execute(
            "SELECT id, name, sku, price, quantity FROM products ORDER BY id"
        ).fetchall()
    return [as_product(row) for row in rows]


@app.get("/products/{product_id}")
def get_product(product_id: int):
    with connect() as conn:
        row = conn.execute(
            "SELECT id, name, sku, price, quantity FROM products WHERE id = %s",
            (product_id,),
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return as_product(row)


@app.put("/products/{product_id}")
def update_product(product_id: int, product: ProductInput):
    try:
        with connect() as conn:
            row = conn.execute(
                "UPDATE products SET name=%s, sku=%s, price=%s, quantity=%s WHERE id=%s RETURNING id, name, sku, price, quantity",
                (product.name, product.sku, product.price, product.quantity, product_id),
            ).fetchone()
        if row is None:
            raise HTTPException(status_code=404, detail="Product not found")
        return as_product(row)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(status_code=409, detail="SKU already exists")


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    with connect() as conn:
        result = conn.execute("DELETE FROM products WHERE id = %s", (product_id,))
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return Response(status_code=204)
