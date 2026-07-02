# API Reference

The FastAPI demo app exposes both shop APIs and an AI diagnosis API.

Run the app locally:

```powershell
uvicorn app.main:app --reload
```

Base URL:

```text
http://127.0.0.1:8000
```

FastAPI also exposes interactive docs at:

```text
http://127.0.0.1:8000/docs
```

## Health

### `GET /health`

Returns service health.

Response:

```json
{
  "status": "ok"
}
```

## Auth

### `POST /api/login`

Request:

```json
{
  "username": "alice",
  "password": "password123"
}
```

Response:

```json
{
  "access_token": "demo-token:alice",
  "token_type": "bearer"
}
```

Invalid credentials return HTTP `401`.

## Products

### `GET /api/products`

Returns the product catalog.

### `GET /api/products/{product_id}`

Returns one product by id.

Missing products return HTTP `404`.

## Orders

### `POST /api/orders`

Requires:

```text
Authorization: Bearer demo-token:alice
```

Request:

```json
{
  "product_id": 1,
  "quantity": 1
}
```

Response:

```json
{
  "id": 1,
  "username": "alice",
  "product_id": 1,
  "product_name": "Wireless Mouse",
  "quantity": 1,
  "status": "created"
}
```

Missing authorization returns HTTP `401`.

Insufficient stock returns HTTP `409`.

## AI Diagnosis

### `POST /api/diagnosis`

Generates a diagnosis report from one failure artifact.

Request:

```json
{
  "nodeid": "tests/api/test_orders_api.py::test_create_order",
  "failed_at": "2026-07-02T10:00:00+00:00",
  "phase": "call",
  "duration_seconds": 0.12,
  "longrepr": "AssertionError: expected 409 but got 500",
  "keywords": ["api", "orders"]
}
```

Response:

```json
{
  "artifact_count": 1,
  "report_markdown": "## Summary\n\n..."
}
```

If `OPENAI_API_KEY` is not configured, the endpoint returns a fallback report. This keeps the API demo usable without secrets.
