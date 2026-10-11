from fastapi import FastAPI, HTTPException
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI(title="ShopFlow Catalog API", version="0.1.0")
REQUESTS = Counter("catalog_http_requests_total", "Catalog API HTTP requests", ["route"])
PRODUCTS = [
    {"id": "sku-001", "name": "Mechanical Keyboard", "price": 79.99},
    {"id": "sku-002", "name": "USB-C Hub", "price": 34.50},
    {"id": "sku-003", "name": "Monitor Stand", "price": 42.00},
]

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    return {"status": "ready"}

@app.get("/products")
def products():
    REQUESTS.labels(route="/products").inc()
    return {"items": PRODUCTS, "count": len(PRODUCTS)}

@app.get("/products/{product_id}")
def product(product_id: str):
    REQUESTS.labels(route="/products/{product_id}").inc()
    for item in PRODUCTS:
        if item["id"] == product_id:
            return item
    raise HTTPException(status_code=404, detail="Product not found")

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
