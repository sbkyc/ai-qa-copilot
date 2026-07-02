import os
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import connect, initialize_database, seed_database
from app.schemas import (
    DiagnosisRequest,
    DiagnosisResponse,
    LoginRequest,
    LoginResponse,
    OrderRequest,
)
from app.services import (
    AuthenticationError,
    InsufficientStockError,
    ProductNotFoundError,
    authenticate_user,
    create_order,
    get_product,
    list_products,
    token_for_username,
    username_from_token,
)
from qa_copilot.artifacts import FailureArtifact
from qa_copilot.diagnosis import diagnose_with_ai
from qa_copilot.prompt_builder import build_diagnosis_prompt

templates = Jinja2Templates(directory="app/templates")


def _resolve_db_path(db_path: str | Path | None) -> str | Path:
    if db_path is not None:
        return db_path
    return os.getenv("AI_QA_DB_PATH", "reports/latest/dev.sqlite")


def _extract_bearer_token(authorization: str | None) -> str:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return authorization.removeprefix("Bearer ").strip()


def create_app(db_path: str | Path | None = None) -> FastAPI:
    resolved_db_path = _resolve_db_path(db_path)

    @asynccontextmanager
    async def lifespan(api: FastAPI) -> AsyncIterator[None]:
        if resolved_db_path != ":memory:":
            Path(resolved_db_path).parent.mkdir(parents=True, exist_ok=True)
        connection = connect(resolved_db_path)
        initialize_database(connection)
        seed_database(connection)
        api.state.db = connection
        try:
            yield
        finally:
            connection.close()

    api = FastAPI(title="AI QA Copilot Demo Shop", lifespan=lifespan)
    api.mount("/static", StaticFiles(directory="app/static"), name="static")

    def get_db() -> sqlite3.Connection:
        return api.state.db

    def current_username(authorization: str | None = Header(default=None)) -> str:
        token = _extract_bearer_token(authorization)
        try:
            return username_from_token(token)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc

    DbConnection = Annotated[sqlite3.Connection, Depends(get_db)]
    CurrentUsername = Annotated[str, Depends(current_username)]

    @api.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @api.post("/api/login", response_model=LoginResponse)
    def login(payload: LoginRequest, db: DbConnection) -> LoginResponse:
        try:
            user = authenticate_user(db, payload.username, payload.password)
        except AuthenticationError as exc:
            raise HTTPException(status_code=401, detail=str(exc)) from exc
        return LoginResponse(access_token=token_for_username(user["username"]))

    @api.get("/api/products")
    def products(db: DbConnection) -> list[dict[str, object]]:
        return list_products(db)

    @api.get("/api/products/{product_id}")
    def product_detail(
        product_id: int,
        db: DbConnection,
    ) -> dict[str, object]:
        try:
            return get_product(db, product_id)
        except ProductNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @api.post("/api/orders", status_code=201)
    def order_create(
        payload: OrderRequest,
        username: CurrentUsername,
        db: DbConnection,
    ) -> dict[str, object]:
        try:
            return create_order(db, username, payload.product_id, payload.quantity)
        except ProductNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InsufficientStockError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @api.post("/api/diagnosis", response_model=DiagnosisResponse)
    def diagnosis_create(payload: DiagnosisRequest) -> DiagnosisResponse:
        artifact = FailureArtifact(
            nodeid=payload.nodeid,
            failed_at=payload.failed_at,
            phase=payload.phase,
            duration_seconds=payload.duration_seconds,
            longrepr=payload.longrepr,
            keywords=payload.keywords,
        )
        prompt = build_diagnosis_prompt([artifact])
        report = diagnose_with_ai(prompt)
        return DiagnosisResponse(artifact_count=1, report_markdown=report)

    @api.get("/", response_class=HTMLResponse)
    def login_page(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(request, "login.html", {"error": ""})

    @api.post("/login", response_model=None)
    async def web_login(
        request: Request,
        db: DbConnection,
    ) -> HTMLResponse | RedirectResponse:
        form = await request.form()
        username = str(form.get("username", ""))
        password = str(form.get("password", ""))
        try:
            authenticate_user(db, username, password)
        except AuthenticationError:
            return templates.TemplateResponse(
                request,
                "login.html",
                {"error": "Invalid username or password"},
                status_code=401,
            )
        response = RedirectResponse("/products", status_code=303)
        response.set_cookie("qa_user", username, httponly=True)
        return response

    @api.get("/products", response_class=HTMLResponse, response_model=None)
    def products_page(
        request: Request,
        db: DbConnection,
    ) -> HTMLResponse | RedirectResponse:
        username = request.cookies.get("qa_user")
        if not username:
            return RedirectResponse("/", status_code=303)
        return templates.TemplateResponse(
            request,
            "products.html",
            {"username": username, "products": list_products(db), "error": ""},
        )

    @api.post("/orders", response_model=None)
    async def web_order(
        request: Request,
        db: DbConnection,
    ) -> HTMLResponse | RedirectResponse:
        username = request.cookies.get("qa_user")
        if not username:
            return RedirectResponse("/", status_code=303)
        form = await request.form()
        product_id = int(str(form.get("product_id", "0")))
        quantity = int(str(form.get("quantity", "1")))
        try:
            order = create_order(db, username, product_id, quantity)
        except (ProductNotFoundError, InsufficientStockError) as exc:
            return templates.TemplateResponse(
                request,
                "products.html",
                {
                    "username": username,
                    "products": list_products(db),
                    "error": str(exc),
                },
                status_code=409,
            )
        return templates.TemplateResponse(
            request,
            "order_success.html",
            {"username": username, "order": order},
        )

    return api


app = create_app()
