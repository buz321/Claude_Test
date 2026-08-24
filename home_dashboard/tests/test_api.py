"""API CRUD 및 대시보드 요약 테스트."""

from datetime import date, timedelta


def app_today(client) -> date:
    """서버가 보는 오늘 날짜 (설정된 타임존 기준)."""
    return date.fromisoformat(client.get("/api/health").json()["today"])


def test_health(client):
    body = client.get("/api/health").json()
    assert body["status"] == "ok"
    assert body["scheduler"] is False


def test_task_crud(client):
    created = client.post("/api/tasks", json={"title": "분리수거", "assignee": "아빠"}).json()
    assert created["title"] == "분리수거"
    assert created["done"] == 0

    task_id = created["id"]
    done = client.patch(f"/api/tasks/{task_id}", json={"done": True}).json()
    assert done["done"] == 1
    assert done["completed_at"] is not None

    undone = client.patch(f"/api/tasks/{task_id}", json={"done": False}).json()
    assert undone["done"] == 0
    assert undone["completed_at"] is None

    assert client.get("/api/tasks?include_done=false").json()
    assert client.delete(f"/api/tasks/{task_id}").status_code == 204
    assert client.get("/api/tasks").json() == []


def test_repeating_task_rolls_forward(client):
    today = app_today(client)
    task = client.post(
        "/api/tasks", json={"title": "쓰레기 버리기", "due_date": today.isoformat(), "repeat": "weekly"}
    ).json()

    rolled = client.patch(f"/api/tasks/{task['id']}", json={"done": True}).json()
    assert rolled["done"] == 0  # 반복 할일은 완료 대신 다음 주기로
    assert rolled["due_date"] == (today + timedelta(days=7)).isoformat()


def test_empty_date_string_becomes_null(client):
    task = client.post("/api/tasks", json={"title": "언젠가", "due_date": "", "due_time": ""}).json()
    assert task["due_date"] is None
    assert task["due_time"] is None


def test_shopping_flow(client):
    item = client.post("/api/shopping", json={"name": "우유", "quantity": "2팩", "urgent": True}).json()
    assert item["urgent"] == 1

    bought = client.patch(f"/api/shopping/{item['id']}", json={"bought": True}).json()
    assert bought["bought"] == 1
    assert bought["bought_at"] is not None

    assert client.post("/api/shopping/clear-bought").json() == {"deleted": 1}
    assert client.get("/api/shopping").json() == []


def test_event_crud(client):
    event = client.post(
        "/api/events", json={"title": "아빠 생일", "date": "2026-09-01", "start_time": "19:00"}
    ).json()
    assert event["title"] == "아빠 생일"

    patched = client.patch(f"/api/events/{event['id']}", json={"location": "집"}).json()
    assert patched["location"] == "집"
    assert client.delete(f"/api/events/{event['id']}").status_code == 204


def test_summary_buckets(client):
    # 서버 타임존(기본 Asia/Seoul) 기준 '오늘'을 써야 버킷이 맞습니다.
    today = app_today(client)
    yesterday = (today - timedelta(days=1)).isoformat()
    in_three_days = (today + timedelta(days=3)).isoformat()

    client.post("/api/tasks", json={"title": "지난 할일", "due_date": yesterday})
    client.post("/api/tasks", json={"title": "오늘 할일", "due_date": today.isoformat()})
    client.post("/api/tasks", json={"title": "나중에"})
    client.post("/api/events", json={"title": "오늘 일정", "date": today.isoformat()})
    client.post("/api/events", json={"title": "주중 일정", "date": in_three_days})
    client.post("/api/shopping", json={"name": "계란"})

    summary = client.get("/api/summary").json()
    assert [t["title"] for t in summary["overdue_tasks"]] == ["지난 할일"]
    assert [t["title"] for t in summary["today_tasks"]] == ["오늘 할일"]
    assert [t["title"] for t in summary["someday_tasks"]] == ["나중에"]
    assert [e["title"] for e in summary["week_events"]] == ["주중 일정"]
    assert summary["counts"] == {"overdue": 1, "today_tasks": 1, "today_events": 1, "shopping": 1}


def test_missing_item_returns_404(client):
    assert client.patch("/api/tasks/999", json={"done": True}).status_code == 404
    assert client.delete("/api/events/999").status_code == 404


def test_index_page_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "우리집" in response.text
