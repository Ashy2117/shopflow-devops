import os, time
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import psycopg
from psycopg.rows import dict_row
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI(title="ShopFlow Orders API", version="0.1.0")
REQUESTS = Counter("orders_http_requests_total", "Orders API HTTP requests", ["route"])
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://shopflow:lab-only-change-me@postgres:5432/shopflow")

def connect():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row, connect_timeout=3)

def init_db():
    with connect() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS orders (id BIGSERIAL PRIMARY KEY, product_id TEXT NOT NULL, quantity INTEGER NOT NULL CHECK (quantity > 0), created_at TIMESTAMPTZ NOT NULL DEFAULT NOW())")

@app.on_event("startup")
def startup():
    last_error = None
    for attempt in range(12):
        try:
            init_db()
            return
        except Exception as exc:
            last_error = exc
            time.sleep(min(2 + attempt, 5))
    raise RuntimeError(f"Database initialization failed: {last_error}")

class OrderIn(BaseModel):
    product_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=1000)

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    try:
        with connect() as conn:
            conn.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database not ready")

@app.get("/orders")
def list_orders():
    REQUESTS.labels(route="/orders").inc()
    with connect() as conn:
        rows = conn.execute("SELECT id, product_id, quantity, created_at FROM orders ORDER BY id DESC LIMIT 100").fetchall()
    return {"items": rows, "count": len(rows)}

@app.post("/orders", status_code=201)
def create_order(order: OrderIn):
    REQUESTS.labels(route="/orders POST").inc()
    with connect() as conn:
        row = conn.execute("INSERT INTO orders (product_id, quantity) VALUES (%s, %s) RETURNING id, product_id, quantity, created_at", (order.product_id, order.quantity)).fetchone()
    return row

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
