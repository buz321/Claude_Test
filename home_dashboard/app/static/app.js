"use strict";

const WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"];
let showDone = false;

// ------------------------------------------------------------------ 유틸리티
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    toast("오류가 났어요 (" + response.status + ")");
    throw new Error(path + " -> " + response.status);
  }
  return response.status === 204 ? null : response.json();
}

function toast(message) {
  const el = document.getElementById("toast");
  el.textContent = message;
  el.classList.add("show");
  clearTimeout(toast._timer);
  toast._timer = setTimeout(() => el.classList.remove("show"), 2000);
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function fmtDate(iso) {
  if (!iso) return "";
  const d = new Date(iso + "T00:00:00");
  if (Number.isNaN(d.getTime())) return iso;
  return `${d.getMonth() + 1}/${d.getDate()}(${WEEKDAYS[(d.getDay() + 6) % 7]})`;
}

function todayISO() {
  const now = new Date();
  const offset = now.getTimezoneOffset() * 60000;
  return new Date(now - offset).toISOString().slice(0, 10);
}

function formData(form) {
  const data = {};
  for (const el of form.elements) {
    if (!el.name) continue;
    data[el.name] = el.type === "checkbox" ? el.checked : el.value;
  }
  return data;
}

// -------------------------------------------------------------------- 렌더링
function taskItem(task, opts = {}) {
  const overdue = task.due_date && task.due_date < todayISO() && !task.done;
  const meta = [];
  if (task.due_date) meta.push(fmtDate(task.due_date));
  if (task.due_time) meta.push(task.due_time);
  if (task.assignee) meta.push("👤 " + task.assignee);
  if (task.repeat && task.repeat !== "none") {
    meta.push({ daily: "매일", weekly: "매주", monthly: "매월" }[task.repeat]);
  }
  if (task.note) meta.push(task.note);
  return `
    <div class="item ${task.done ? "done" : ""} ${overdue && opts.markOverdue !== false ? "overdue" : ""}">
      <input type="checkbox" ${task.done ? "checked" : ""}
             onchange="toggleTask(${task.id}, this.checked)">
      <div class="body">
        <div class="title">${esc(task.title)}
          ${overdue ? '<span class="badge red">지남</span>' : ""}</div>
        ${meta.length ? `<div class="meta">${esc(meta.join(" · "))}</div>` : ""}
      </div>
      <button class="del" onclick="removeItem('tasks', ${task.id})">✕</button>
    </div>`;
}

function eventItem(event) {
  const meta = [fmtDate(event.date)];
  if (event.start_time) meta.push(event.start_time + (event.end_time ? "~" + event.end_time : ""));
  if (event.location) meta.push("📍 " + event.location);
  if (event.note) meta.push(event.note);
  const isToday = event.date === todayISO();
  return `
    <div class="item">
      <div class="body">
        <div class="title">${esc(event.title)}
          ${isToday ? '<span class="badge blue">오늘</span>' : ""}</div>
        <div class="meta">${esc(meta.join(" · "))}</div>
      </div>
      <button class="del" onclick="removeItem('events', ${event.id})">✕</button>
    </div>`;
}

function shoppingItem(item) {
  const meta = [item.quantity, item.note].filter(Boolean).join(" · ");
  return `
    <div class="item ${item.bought ? "done" : ""} ${item.urgent && !item.bought ? "urgent" : ""}">
      <input type="checkbox" ${item.bought ? "checked" : ""}
             onchange="toggleShopping(${item.id}, this.checked)">
      <div class="body">
        <div class="title">${esc(item.name)}
          ${item.urgent ? '<span class="badge warn">급함</span>' : ""}</div>
        ${meta ? `<div class="meta">${esc(meta)}</div>` : ""}
      </div>
      <button class="del" onclick="removeItem('shopping', ${item.id})">✕</button>
    </div>`;
}

function section(title, items, renderer, emptyText) {
  const body = items.length
    ? items.map(renderer).join("")
    : `<div class="empty">${emptyText}</div>`;
  return `<h2>${title}</h2>${body}`;
}

// --------------------------------------------------------------------- 로딩
async function loadToday() {
  const data = await api("/api/summary");
  const counts = data.counts;
  document.getElementById("today-label").textContent = fmtDate(data.today);

  document.getElementById("stats").innerHTML = `
    <div class="stat ${counts.overdue ? "alert" : ""}">
      <span class="num">${counts.overdue}</span><span class="lbl">지난 할일</span></div>
    <div class="stat"><span class="num">${counts.today_tasks}</span><span class="lbl">오늘 할일</span></div>
    <div class="stat"><span class="num">${counts.today_events}</span><span class="lbl">오늘 일정</span></div>
    <div class="stat"><span class="num">${counts.shopping}</span><span class="lbl">살 것</span></div>`;

  let html = "";
  if (data.overdue_tasks.length) {
    html += section("⚠️ 지난 할일", data.overdue_tasks, taskItem, "");
  }
  html += section("✅ 오늘 할일", data.today_tasks, taskItem, "오늘 할일이 없어요 🎉");
  html += section("📅 오늘 일정", data.today_events, eventItem, "오늘 일정 없음");
  html += section("🗓 이번 주 일정", data.week_events, eventItem, "이번 주 일정 없음");
  html += section("🛒 살 것", data.shopping.slice(0, 8), shoppingItem, "장보기 목록 비어 있음");
  if (data.upcoming_tasks.length) {
    html += section("📌 다가오는 할일", data.upcoming_tasks, (t) => taskItem(t, { markOverdue: false }), "");
  }
  if (data.someday_tasks.length) {
    html += section("🗒 날짜 없는 할일", data.someday_tasks, taskItem, "");
  }
  document.getElementById("today-content").innerHTML = html;
}

async function loadTasks() {
  const tasks = await api("/api/tasks?include_done=" + showDone);
  document.getElementById("task-list").innerHTML = tasks.length
    ? tasks.map((t) => taskItem(t)).join("")
    : '<div class="empty">할일이 없습니다.</div>';
}

async function loadShopping() {
  const items = await api("/api/shopping");
  document.getElementById("shopping-list").innerHTML = items.length
    ? items.map(shoppingItem).join("")
    : '<div class="empty">살 것이 없습니다.</div>';
}

async function loadEvents() {
  const events = await api("/api/events?upcoming_only=true");
  document.getElementById("event-list").innerHTML = events.length
    ? events.map(eventItem).join("")
    : '<div class="empty">예정된 일정이 없습니다.</div>';
}

async function refresh() {
  const active = document.querySelector(".tab.active").dataset.tab;
  const loaders = { today: loadToday, tasks: loadTasks, shopping: loadShopping, events: loadEvents };
  await loaders[active]();
}

// ----------------------------------------------------------------- 이벤트 핸들러
async function toggleTask(id, done) {
  await api(`/api/tasks/${id}`, { method: "PATCH", body: JSON.stringify({ done }) });
  refresh();
}

async function toggleShopping(id, bought) {
  await api(`/api/shopping/${id}`, { method: "PATCH", body: JSON.stringify({ bought }) });
  refresh();
}

async function removeItem(kind, id) {
  await api(`/api/${kind}/${id}`, { method: "DELETE" });
  refresh();
}

function bindForm(formId, endpoint, defaults = {}) {
  document.getElementById(formId).addEventListener("submit", async (event) => {
    event.preventDefault();
    const form = event.target;
    await api(endpoint, { method: "POST", body: JSON.stringify({ ...defaults, ...formData(form) }) });
    form.reset();
    toast("추가했어요");
    refresh();
  });
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach((t) => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
    tab.classList.add("active");
    document.getElementById("tab-" + tab.dataset.tab).classList.add("active");
    refresh();
  });
});

document.getElementById("show-done").addEventListener("change", (event) => {
  showDone = event.target.checked;
  loadTasks();
});

document.getElementById("btn-clear-bought").addEventListener("click", async () => {
  const result = await api("/api/shopping/clear-bought", { method: "POST" });
  toast(`${result.deleted}개 정리했어요`);
  refresh();
});

document.getElementById("btn-notify").addEventListener("click", async () => {
  const result = await api("/api/notify/digest", { method: "POST" });
  toast(result.sent ? `알림 보냄 (${result.channel})` : "알림 실패 - 설정 확인");
});

bindForm("task-form", "/api/tasks");
bindForm("shopping-form", "/api/shopping");
bindForm("event-form", "/api/events");

// 첫 로딩 + 탭이 다시 보일 때 자동 새로고침
loadToday();
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refresh();
});
setInterval(() => { if (!document.hidden) refresh(); }, 60000);
