"""Cliente mínimo do Supabase/PostgREST usando HTTPX.

A aplicação usa a secret key exclusivamente no backend e a envia somente no
cabeçalho `apikey`, conforme o formato atual das chaves `sb_secret_...`.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any
from urllib.parse import quote

import httpx

from app.core.config import Settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)


def _value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


@dataclass
class QueryResult:
    data: list[dict[str, Any]]
    count: int | None = None


class PostgrestQuery:
    def __init__(self, repo: "SupabaseRepository", table: str):
        self.repo = repo
        self.table = table
        self.params: list[tuple[str, str]] = []
        self._count_exact = False

    def select(self, columns: str = "*", count: str | None = None):
        self.params.append(("select", columns))
        self._count_exact = count == "exact"
        return self

    def _filter(self, column: str, operator: str, value: Any):
        self.params.append((column, f"{operator}.{_value(value)}"))
        return self

    def eq(self, column: str, value: Any): return self._filter(column, "eq", value)
    def gt(self, column: str, value: Any): return self._filter(column, "gt", value)
    def gte(self, column: str, value: Any): return self._filter(column, "gte", value)
    def lt(self, column: str, value: Any): return self._filter(column, "lt", value)
    def lte(self, column: str, value: Any): return self._filter(column, "lte", value)
    def ilike(self, column: str, value: str): return self._filter(column, "ilike", value)

    def is_(self, column: str, value: str):
        self.params.append((column, f"is.{value}"))
        return self

    def in_(self, column: str, values: list[Any]):
        encoded = ",".join(quote(_value(v), safe="-_.~") for v in values)
        self.params.append((column, f"in.({encoded})"))
        return self

    def limit(self, value: int):
        self.params.append(("limit", str(value)))
        return self

    def order(self, column: str, desc: bool = False):
        self.params.append(("order", f"{column}.{'desc' if desc else 'asc'}"))
        return self

    def execute(self) -> QueryResult:
        return self.repo._get(self.table, self.params, count_exact=self._count_exact)


class SupabaseRepository:
    def __init__(self, settings: Settings):
        if not settings.supabase_url or not settings.supabase_secret_key:
            raise AppError("Supabase não configurado. Preencha SUPABASE_URL e SUPABASE_SECRET_KEY.", 503)
        self.base_url = settings.supabase_url.rstrip("/") + "/rest/v1"
        self.headers = {
            "apikey": settings.supabase_secret_key,
            "Content-Type": "application/json",
            "User-Agent": "gamificacao-qr-backend/0.1",
        }
        self.timeout = httpx.Timeout(15.0, connect=8.0)

    def _request(self, method: str, path: str, *, params=None, json=None, headers=None) -> httpx.Response:
        merged = {**self.headers, **(headers or {})}
        try:
            with httpx.Client(base_url=self.base_url, headers=merged, timeout=self.timeout) as client:
                response = client.request(method, path, params=params, json=json)
            if response.status_code >= 400:
                logger.error("Supabase %s %s -> %s: %s", method, path, response.status_code, response.text[:500])
                raise AppError("Falha ao acessar o banco de dados.", 503)
            return response
        except AppError:
            raise
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            logger.exception("Falha de rede ao acessar Supabase")
            raise AppError("Banco de dados temporariamente indisponível.", 503) from exc

    def _get(self, table: str, params: list[tuple[str, str]], *, count_exact: bool = False) -> QueryResult:
        headers = {"Prefer": "count=exact"} if count_exact else None
        response = self._request("GET", f"/{table}", params=params, headers=headers)
        count = None
        if count_exact:
            content_range = response.headers.get("content-range", "")
            if "/" in content_range:
                total = content_range.rsplit("/", 1)[-1]
                count = int(total) if total.isdigit() else None
        return QueryResult(data=response.json() if response.content else [], count=count)

    def raw_table(self, table: str) -> PostgrestQuery:
        return PostgrestQuery(self, table)

    def select(self, table: str, columns: str = "*", **filters: Any) -> list[dict[str, Any]]:
        query = self.raw_table(table).select(columns)
        for key, value in filters.items():
            query.eq(key, value)
        return query.execute().data

    def insert(self, table: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = self._request("POST", f"/{table}", json=payload, headers={"Prefer": "return=representation"})
        data = response.json() if response.content else []
        if not data:
            raise AppError("O banco não retornou o registro criado.", 503)
        return data[0]

    def update(self, table: str, payload: dict[str, Any], **filters: Any) -> list[dict[str, Any]]:
        params = [(key, f"eq.{_value(value)}") for key, value in filters.items()]
        response = self._request("PATCH", f"/{table}", params=params, json=payload, headers={"Prefer": "return=representation"})
        return response.json() if response.content else []

    def delete(self, table: str, **filters: Any) -> None:
        params = [(key, f"eq.{_value(value)}") for key, value in filters.items()]
        self._request("DELETE", f"/{table}", params=params, headers={"Prefer": "return=minimal"})
