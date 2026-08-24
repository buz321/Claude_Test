"""FastAPI 앱: 집안 대시보드 API + 웹 UI."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import digest, repository
from .config import Settings, load_settings
from .db import connect, init_db
from .models import EventIn, EventPatch, ShoppingIn, ShoppingPatch, TaskIn, TaskPatch
from .notifier import build_notifier
from .scheduler import send_digest

logger = logging.getLogger(__name__)
STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    tz = ZoneInfo(settings.timezone)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(settings.db_path)
        init_db(conn)
        app.state.conn = conn
        app.state.settings = settings
        app.state.notifier = build_notifier(settings)
        app.state.scheduler = None
        if settings.scheduler_enabled:
            from .scheduler import start_scheduler

            app.state.scheduler = start_scheduler(conn, app.state.notifier, settings)
        try:
            yield
        finally:
            if app.state.scheduler is not None:
                app.state.scheduler.shutdown(wait=False)
            conn.close()

    app = FastAPI(title="집안 대시보드", version="0.1.0", lifespan=lifespan)

    def db():
        return app.state.conn

    def today():
        return datetime.now(tz).date()

    def found(value: Any, name: str = "항목") -> Any:
        if value is None:
            raise HTTPException(status_code=404, detail=f"{name}을(를) 찾을 수 없습니다.")
        return value

    # ------------------------------------------------------------------ 대시보드
    @app.get("/api/summary")
    def get_summary() -> dict[str, Any]:
        return repository.summary(db(), today())

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "today": today().isoformat(),
            "notifier": app.state.notifier.name,
            "scheduler": app.state.scheduler is not None,
        }

    # ---------------------------------------------------------------------- 할일
    @app.get("/api/tasks")
    def get_tasks(include_done: bool = True) -> list[dict[str, Any]]:
        return repository.list_tasks(db(), include_done=include_done)

    @app.post("/api/tasks", status_code=201)
    def post_task(payload: TaskIn) -> dict[str, Any]:
        return repository.create_task(db(), payload.model_dump())

    @app.patch("/api/tasks/{task_id}")
    def patch_task(task_id: int, payload: TaskPatch) -> dict[str, Any]:
        updated = repository.update_task(db(), task_id, payload.model_dump(exclude_unset=True))
        return found(updated, "할일")

    @app.delete("/api/tasks/{task_id}", status_code=204)
    def remove_task(task_id: int) -> None:
        found(repository.delete_task(db(), task_id) or None, "할일")

    # -------------------------------------------------------------------- 장보기
    @app.get("/api/shopping")
    def get_shopping_items() -> list[dict[str, Any]]:
        return repository.list_shopping(db())

    @app.post("/api/shopping", status_code=201)
    def post_shopping(payload: ShoppingIn) -> dict[str, Any]:
        return repository.create_shopping(db(), payload.model_dump())

    @app.patch("/api/shopping/{item_id}")
    def patch_shopping(item_id: int, payload: ShoppingPatch) -> dict[str, Any]:
        updated = repository.update_shopping(db(), item_id, payload.model_dump(exclude_unset=True))
        return found(updated, "장보기 항목")

    @app.delete("/api/shopping/{item_id}", status_code=204)
    def remove_shopping(item_id: int) -> None:
        found(repository.delete_shopping(db(), item_id) or None, "장보기 항목")

    @app.post("/api/shopping/clear-bought")
    def clear_bought() -> dict[str, int]:
        return {"deleted": repository.clear_bought(db())}

    # ---------------------------------------------------------------------- 일정
    @app.get("/api/events")
    def get_events(upcoming_only: bool = False) -> list[dict[str, Any]]:
        return repository.list_events(db(), since=today().isoformat() if upcoming_only else None)

    @app.post("/api/events", status_code=201)
    def post_event(payload: EventIn) -> dict[str, Any]:
        return repository.create_event(db(), payload.model_dump())

    @app.patch("/api/events/{event_id}")
    def patch_event(event_id: int, payload: EventPatch) -> dict[str, Any]:
        updated = repository.update_event(db(), event_id, payload.model_dump(exclude_unset=True))
        return found(updated, "일정")

    @app.delete("/api/events/{event_id}", status_code=204)
    def remove_event(event_id: int) -> None:
        found(repository.delete_event(db(), event_id) or None, "일정")

    # ---------------------------------------------------------------------- 알림
    @app.get("/api/notify/preview")
    def notify_preview() -> dict[str, str]:
        title, body = digest.build_digest(repository.summary(db(), today()))
        return {"title": title, "body": body}

    @app.post("/api/notify/digest")
    def notify_digest() -> dict[str, Any]:
        ok = send_digest(db(), app.state.notifier, today())
        return {"sent": ok, "channel": app.state.notifier.name}

    # ------------------------------------------------------------------- 정적 UI
    if STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

        @app.get("/", include_in_schema=False)
        def index() -> FileResponse:
            return FileResponse(STATIC_DIR / "index.html")

        @app.get("/manifest.webmanifest", include_in_schema=False)
        def manifest() -> FileResponse:
            return FileResponse(STATIC_DIR / "manifest.webmanifest")

    return app


app = create_app()


def main() -> None:
    """`home-dashboard` 실행 진입점."""
    import uvicorn

    settings = load_settings()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run(app, host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()
