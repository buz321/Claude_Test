"use strict";

/* =========================================================================
 * 우리집 대시보드 — 모바일 우선 프런트엔드
 * 서버 API(/api/*)만 쓰고 빌드 도구 없이 동작합니다.
 * ========================================================================= */

const WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"];
const RING_LENGTH = 213.63;               // 2πr (r=34)
const FREQUENT = ["우유", "계란", "휴지", "쌀", "세제", "물", "빵", "과일"];
const REPEAT_LABEL = { none: "", daily: "매일", weekly: "매주", monthly: "매월" };

const state = {
  tab: "today",
  taskFilter: "todo",
  summary: null,
  tasks: [],
  shopping: [],
  events: [],
  loaded: false,
};

const $ = (selector) => document.querySelector(selector);
const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ------------------------------------------------------------------ 유틸 */
async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    toast("문제가 생겼어요 (" + response.status + ")");
    throw new Error(path + " -> " + response.status);
  }
  return response.status === 204 ? null : response.json();
}

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function buzz(pattern = 8) {
  if (navigator.vibrate && !reduceMotion) navigator.vibrate(pattern);
}

function todayISO() {
  return state.summary ? state.summary.today : localISO(new Date());
}

function localISO(date) {
  const offset = date.getTimezoneOffset() * 60000;
  return new Date(date - offset).toISOString().slice(0, 10);
}

function shiftDays(iso, days) {
  const date = new Date(iso + "T00:00:00");
  date.setDate(date.getDate() + days);
  return localISO(date);
}

function dayDiff(iso) {
  return Math.round(
    (new Date(iso + "T00:00:00") - new Date(todayISO() + "T00:00:00")) / 86400000
  );
}

/** '2026-08-25' → '오늘' / '내일' / '8/28(금)' */
function dayLabel(iso) {
  if (!iso) return "";
  const diff = dayDiff(iso);
  if (diff === 0) return "오늘";
  if (diff === 1) return "내일";
  if (diff === -1) return "어제";
  const date = new Date(iso + "T00:00:00");
  const weekday = WEEKDAYS[(date.getDay() + 6) % 7];
  const base = `${date.getMonth() + 1}/${date.getDate()}(${weekday})`;
  return diff < 0 ? `${base} · ${-diff}일 지남` : base;
}

/** '20:00' → { label: '오후', text: '8:00' } */
function ampm(value) {
  const [hour, minute] = value.split(":").map(Number);
  return {
    label: hour < 12 ? "오전" : "오후",
    text: `${hour % 12 || 12}:${String(minute).padStart(2, "0")}`,
  };
}

function fmtTime(value) {
  if (!value) return "";
  const { label, text } = ampm(value);
  return `${label} ${text}`;
}

/* ------------------------------------------------------------- 토스트/실행취소 */
let toastTimer = null;

function toast(message, action = null) {
  const el = $("#toast");
  el.innerHTML = `<span>${esc(message)}</span>`;
  if (action) {
    const button = document.createElement("button");
    button.textContent = action.label;
    button.onclick = () => { hideToast(); action.run(); };
    el.appendChild(button);
  }
  el.classList.add("on");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(hideToast, action ? 5000 : 2200);
}

function hideToast() {
  $("#toast").classList.remove("on");
}

/* ------------------------------------------------------------------ 테마 */
function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  $("#theme-icon").textContent = theme === "dark" ? "☀" : "☾";
  const color = theme === "dark" ? "#0e1116" : "#4b6ef5";
  document.querySelector('meta[name="theme-color"]').setAttribute("content", color);
}

function initTheme() {
  let saved = null;
  try { saved = localStorage.getItem("theme"); } catch { /* 시크릿 모드 */ }
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(saved || (prefersDark ? "dark" : "light"));
}

$("#btn-theme").addEventListener("click", () => {
  const next = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
  applyTheme(next);
  try { localStorage.setItem("theme", next); } catch { /* 무시 */ }
  $("#theme-icon").classList.add("spin");
  setTimeout(() => $("#theme-icon").classList.remove("spin"), 460);
  buzz();
});

/* --------------------------------------------------------------- 렌더 조각 */
function stagger(index) {
  return reduceMotion ? "" : ` style="animation-delay:${Math.min(index * 45, 400)}ms"`;
}

function checkbox(kind, id, checked) {
  return `<span class="check ${checked ? "on" : ""}" data-act="toggle" data-kind="${kind}" data-id="${id}">
    <svg viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5"/></svg></span>`;
}

function swipeWrap(inner, kind, id, index) {
  return `<div class="swipe" data-kind="${kind}" data-id="${id}"${stagger(index)}>
    <div class="swipe-bg">삭제</div>${inner}</div>`;
}

function taskCard(task, index, options = {}) {
  const overdue = !task.done && task.due_date && dayDiff(task.due_date) < 0;
  const meta = [];
  if (task.due_date && options.showDate !== false) meta.push(dayLabel(task.due_date));
  if (task.due_time) meta.push("⏰ " + fmtTime(task.due_time));
  if (task.assignee) meta.push("👤 " + task.assignee);
  if (REPEAT_LABEL[task.repeat]) meta.push("🔁 " + REPEAT_LABEL[task.repeat]);
  if (task.note) meta.push(task.note);

  const inner = `
    <div class="item ${task.done ? "done" : ""} ${overdue ? "overdue" : ""}">
      ${checkbox("tasks", task.id, !!task.done)}
      <div class="body" data-act="edit" data-kind="tasks" data-id="${task.id}">
        <span class="title">${esc(task.title)}</span>
        ${overdue ? ' <span class="pill red">지남</span>' : ""}
        ${meta.length ? `<div class="meta"><span>${meta.map(esc).join("</span><span>")}</span></div>` : ""}
      </div>
    </div>`;
  return swipeWrap(inner, "tasks", task.id, index);
}

function eventCard(event, index, options = {}) {
  const time = event.start_time ? ampm(event.start_time) : null;
  const meta = [];
  if (options.showDate !== false) meta.push(dayLabel(event.date));
  if (event.end_time) meta.push("~ " + fmtTime(event.end_time));
  if (event.location) meta.push("📍 " + event.location);
  if (event.note) meta.push(event.note);

  const inner = `
    <div class="item">
      ${time
        ? `<span class="time-badge"><small>${time.label}</small>${time.text}</span>`
        : `<span class="time-badge"><small>하루</small>종일</span>`}
      <div class="body" data-act="edit" data-kind="events" data-id="${event.id}">
        <span class="title">${esc(event.title)}</span>
        ${dayDiff(event.date) === 0 ? ' <span class="pill">오늘</span>' : ""}
        ${meta.length ? `<div class="meta"><span>${meta.map(esc).join("</span><span>")}</span></div>` : ""}
      </div>
    </div>`;
  return swipeWrap(inner, "events", event.id, index);
}

function shoppingCard(item, index) {
  const meta = [item.quantity, item.note].filter(Boolean);
  const inner = `
    <div class="item ${item.bought ? "done" : ""} ${item.urgent && !item.bought ? "urgent" : ""}">
      ${checkbox("shopping", item.id, !!item.bought)}
      <div class="body" data-act="edit" data-kind="shopping" data-id="${item.id}">
        <span class="title">${esc(item.name)}</span>
        ${item.urgent && !item.bought ? ' <span class="pill warn">급함</span>' : ""}
        ${meta.length ? `<div class="meta"><span>${meta.map(esc).join("</span><span>")}</span></div>` : ""}
      </div>
    </div>`;
  return swipeWrap(inner, "shopping", item.id, index);
}

function sectionHead(label, count, danger = false) {
  return `<div class="sec-head ${danger ? "danger" : ""}">${label}
    ${count ? `<span class="count">${count}</span>` : ""}</div>`;
}

function emptyBox(emoji, text) {
  return `<div class="empty"><span class="big">${emoji}</span>${esc(text)}</div>`;
}

function skeleton(rows = 3) {
  return Array.from({ length: rows }, () => '<div class="sk"></div>').join("");
}

/* -------------------------------------------------------------- 화면 렌더 */
function renderHero() {
  const data = state.summary;
  const counts = data.counts;
  const hour = new Date().getHours();
  const greet =
    hour < 5 ? "늦은 밤이에요" :
    hour < 11 ? "좋은 아침이에요" :
    hour < 14 ? "점심 잘 챙기세요" :
    hour < 18 ? "좋은 오후예요" :
    hour < 22 ? "오늘도 수고했어요" : "편안한 밤 되세요";
  $("#greet").textContent = greet;

  const date = new Date(data.today + "T00:00:00");
  $("#hero-date").textContent =
    `${date.getMonth() + 1}월 ${date.getDate()}일 ${WEEKDAYS[(date.getDay() + 6) % 7]}요일`;

  const total = counts.today_tasks + counts.done_today;
  const percent = total ? Math.round((counts.done_today / total) * 100) : 0;
  $("#ring-fg").style.strokeDashoffset = RING_LENGTH * (1 - percent / 100);
  countUp($("#ring-pct"), percent);

  $("#progress-head").textContent = total
    ? `할일 ${counts.done_today}/${total} 완료`
    : "오늘 할일 없음";
  $("#progress-sub").textContent =
    !total ? "여유로운 하루예요" :
    percent === 100 ? "오늘 할 일 다 끝냈어요 🎉" :
    `${counts.today_tasks}개 남았어요`;

  const chips = [];
  if (counts.overdue) chips.push(`<span class="chip alert">지난 할일 ${counts.overdue}</span>`);
  if (counts.today_events) chips.push(`<span class="chip">오늘 일정 ${counts.today_events}</span>`);
  if (counts.shopping) chips.push(`<span class="chip">살 것 ${counts.shopping}</span>`);
  $("#hero-chips").innerHTML = chips.join("");

  $("#dot-tasks").classList.toggle("on", counts.overdue > 0);
  $("#dot-shopping").classList.toggle("on", counts.shopping > 0);
}

function countUp(el, target) {
  const from = parseInt(el.textContent, 10) || 0;
  if (reduceMotion || from === target) { el.textContent = target + "%"; return; }
  const start = performance.now();
  const step = (now) => {
    const progress = Math.min((now - start) / 700, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.round(from + (target - from) * eased) + "%";
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

function renderToday() {
  const data = state.summary;
  let html = "";
  let index = 0;

  if (data.overdue_tasks.length) {
    html += sectionHead("⚠️ 지난 할일", data.overdue_tasks.length, true);
    html += data.overdue_tasks.map((task) => taskCard(task, index++)).join("");
  }

  html += sectionHead("✅ 오늘 할일", data.today_tasks.length);
  html += data.today_tasks.length
    ? data.today_tasks.map((task) => taskCard(task, index++, { showDate: false })).join("")
    : emptyBox("🎉", data.counts.done_today ? "오늘 할일을 모두 끝냈어요!" : "오늘 등록된 할일이 없어요");

  html += sectionHead("📅 오늘 일정", data.today_events.length);
  html += data.today_events.length
    ? data.today_events.map((event) => eventCard(event, index++, { showDate: false })).join("")
    : emptyBox("🛋", "오늘은 일정이 없어요");

  if (data.week_events.length) {
    html += sectionHead("🗓 다가오는 일정", data.week_events.length);
    html += data.week_events.slice(0, 5).map((event) => eventCard(event, index++)).join("");
  }

  if (data.shopping.length) {
    html += sectionHead("🛒 살 것", data.shopping.length);
    html += data.shopping.slice(0, 5).map((item) => shoppingCard(item, index++)).join("");
    if (data.shopping.length > 5) {
      html += `<button class="linkbtn" data-act="goto" data-tab="shopping">장보기 ${data.shopping.length}개 전체 보기</button>`;
    }
  }

  if (data.upcoming_tasks.length) {
    html += sectionHead("📌 이번 주 할일", data.upcoming_tasks.length);
    html += data.upcoming_tasks.slice(0, 5).map((task) => taskCard(task, index++)).join("");
  }

  if (data.someday_tasks.length) {
    html += sectionHead("🗒 언젠가 할일", data.someday_tasks.length);
    html += data.someday_tasks.slice(0, 5).map((task) => taskCard(task, index++)).join("");
  }

  $("#view-today").innerHTML = html;
}

function renderTasks() {
  const filters = [
    ["todo", "남은 할일"],
    ["today", "오늘"],
    ["overdue", "지남"],
    ["done", "완료"],
  ];
  const segment = `<div class="segment">${filters
    .map(([key, label]) => `<button data-act="filter" data-filter="${key}"
      class="${state.taskFilter === key ? "on" : ""}">${label}</button>`)
    .join("")}</div>`;

  const today = todayISO();
  const list = state.tasks.filter((task) => {
    if (state.taskFilter === "done") return task.done;
    if (task.done) return false;
    if (state.taskFilter === "today") return task.due_date === today;
    if (state.taskFilter === "overdue") return task.due_date && task.due_date < today;
    return true;
  });

  $("#view-tasks").innerHTML = segment + (list.length
    ? list.map((task, index) => taskCard(task, index)).join("")
    : emptyBox("🧺", state.taskFilter === "done" ? "완료한 할일이 없어요" : "할일이 없어요"));
}

function renderShopping() {
  const toBuy = state.shopping.filter((item) => !item.bought);
  const bought = state.shopping.filter((item) => item.bought);

  let html = sectionHead("🛒 살 것", toBuy.length);
  html += toBuy.length
    ? toBuy.map((item, index) => shoppingCard(item, index)).join("")
    : emptyBox("✨", "장보기 목록이 비었어요");

  if (bought.length) {
    html += sectionHead("✔️ 담은 것", bought.length);
    html += bought.map((item, index) => shoppingCard(item, index)).join("");
    html += `<button class="linkbtn" data-act="clear-bought">담은 것 ${bought.length}개 목록에서 비우기</button>`;
  }
  $("#view-shopping").innerHTML = html;
}

function renderEvents() {
  if (!state.events.length) {
    $("#view-events").innerHTML = emptyBox("📅", "예정된 일정이 없어요");
    return;
  }
  // 날짜별로 묶어서 보여줍니다.
  const groups = new Map();
  state.events.forEach((event) => {
    if (!groups.has(event.date)) groups.set(event.date, []);
    groups.get(event.date).push(event);
  });

  let html = "";
  let index = 0;
  groups.forEach((events, date) => {
    html += sectionHead(dayLabel(date), events.length, dayDiff(date) === 0);
    html += events.map((event) => eventCard(event, index++, { showDate: false })).join("");
  });
  $("#view-events").innerHTML = html;
}

/* --------------------------------------------------------------- 데이터 로딩 */
async function load(tab = state.tab, { silent = false } = {}) {
  if (!silent && !state.loaded) {
    document.querySelector(".view.active").innerHTML = skeleton();
  }
  if (tab === "today") {
    state.summary = await api("/api/summary");
    renderHero();
    renderToday();
  } else if (tab === "tasks") {
    const [tasks, summary] = await Promise.all([api("/api/tasks"), api("/api/summary")]);
    state.tasks = tasks;
    state.summary = summary;
    renderHero();
    renderTasks();
  } else if (tab === "shopping") {
    state.shopping = await api("/api/shopping");
    renderShopping();
  } else if (tab === "events") {
    state.events = await api("/api/events?upcoming_only=true");
    renderEvents();
  }
  state.loaded = true;
}

async function refresh(options) {
  await load(state.tab, options);
  if (state.tab !== "today" && state.tab !== "tasks") {
    state.summary = await api("/api/summary");
    renderHero();
  }
}

/* ------------------------------------------------------------------ 탭 이동 */
function moveInk() {
  const active = document.querySelector(".tab.active");
  const ink = $("#tab-ink");
  const rect = active.getBoundingClientRect();
  const parent = active.parentElement.getBoundingClientRect();
  ink.style.transform = `translateX(${rect.left - parent.left + rect.width / 2 - 14}px)`;
}

function switchTab(tab) {
  if (tab === state.tab) { window.scrollTo({ top: 0, behavior: "smooth" }); return; }
  state.tab = tab;
  document.querySelectorAll(".tab").forEach((el) => el.classList.toggle("active", el.dataset.tab === tab));
  document.querySelectorAll(".view").forEach((el) => el.classList.toggle("active", el.id === "view-" + tab));
  moveInk();
  buzz();
  load(tab);
}

$("#tabbar").addEventListener("click", (event) => {
  const tab = event.target.closest(".tab");
  if (tab) switchTab(tab.dataset.tab);
});

/* ------------------------------------------------------------ 항목 조작/스와이프 */
async function toggleItem(kind, id, element) {
  const card = element.closest(".item");
  const turningOn = !element.classList.contains("on");
  element.classList.toggle("on", turningOn);
  card.classList.toggle("done", turningOn);
  if (turningOn) {
    card.classList.add("just-done");
    buzz([10, 40, 14]);
  }
  const field = kind === "tasks" ? "done" : "bought";
  await api(`/api/${kind}/${id}`, { method: "PATCH", body: JSON.stringify({ [field]: turningOn }) });
  setTimeout(() => refresh({ silent: true }), reduceMotion ? 0 : 420);
}

async function deleteItem(kind, id, wrap) {
  const source = { tasks: state.tasks, shopping: state.shopping, events: state.events }[kind];
  const cached = (source || []).find((row) => row.id === id)
    || findInSummary(kind, id);

  wrap.classList.add("removing");
  await api(`/api/${kind}/${id}`, { method: "DELETE" });
  buzz(12);
  setTimeout(() => refresh({ silent: true }), reduceMotion ? 0 : 300);

  if (!cached) { toast("삭제했어요"); return; }
  const payload = { ...cached };
  ["id", "created_at", "completed_at", "bought_at", "done", "bought"].forEach((key) => delete payload[key]);
  toast("삭제했어요", {
    label: "실행취소",
    run: async () => {
      await api(`/api/${kind}`, { method: "POST", body: JSON.stringify(payload) });
      toast("되돌렸어요");
      refresh({ silent: true });
    },
  });
}

function findInSummary(kind, id) {
  const data = state.summary;
  if (!data) return null;
  const buckets = kind === "tasks"
    ? ["overdue_tasks", "today_tasks", "upcoming_tasks", "someday_tasks", "done_today_tasks"]
    : kind === "events" ? ["today_events", "week_events"] : ["shopping"];
  for (const bucket of buckets) {
    const hit = (data[bucket] || []).find((row) => row.id === id);
    if (hit) return hit;
  }
  return null;
}

// 탭/클릭 위임
$("#main").addEventListener("click", (event) => {
  // 스와이프로 끝난 제스처가 클릭으로 이어져 수정 시트가 열리는 것을 막습니다.
  if (Date.now() < suppressClickUntil) { event.stopPropagation(); return; }
  const target = event.target.closest("[data-act]");
  if (!target) return;
  const { act, kind, id } = target.dataset;

  if (act === "toggle") toggleItem(kind, Number(id), target);
  else if (act === "edit") openSheet(kind, Number(id));
  else if (act === "filter") { state.taskFilter = target.dataset.filter; renderTasks(); buzz(); }
  else if (act === "goto") switchTab(target.dataset.tab);
  else if (act === "clear-bought") {
    api("/api/shopping/clear-bought", { method: "POST" }).then((result) => {
      toast(`${result.deleted}개 정리했어요`);
      refresh({ silent: true });
    });
  }
});

// 왼쪽으로 밀어서 삭제
let swipe = null;
let suppressClickUntil = 0;

$("#main").addEventListener("pointerdown", (event) => {
  if (event.target.closest("[data-act='toggle']")) return;
  const wrap = event.target.closest(".swipe");
  if (!wrap) return;
  swipe = { wrap, card: wrap.querySelector(".item"), x: event.clientX, y: event.clientY, dx: 0, axis: null };
});

$("#main").addEventListener("pointermove", (event) => {
  if (!swipe) return;
  const dx = event.clientX - swipe.x;
  const dy = event.clientY - swipe.y;
  if (!swipe.axis) {
    if (Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
    swipe.axis = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
    if (swipe.axis === "x") swipe.card.classList.add("dragging");
  }
  if (swipe.axis !== "x") return;
  swipe.dx = Math.min(0, dx);                       // 왼쪽으로만
  swipe.card.style.transform = `translateX(${swipe.dx}px)`;
  if (swipe.dx < -90 && !swipe.armed) { swipe.armed = true; buzz(10); }
  if (swipe.dx > -90) swipe.armed = false;
});

function endSwipe() {
  if (!swipe) return;
  const { wrap, card, dx, axis } = swipe;
  card.classList.remove("dragging");
  card.style.transform = "";
  const kind = wrap.dataset.kind;
  const id = Number(wrap.dataset.id);
  swipe = null;
  if (axis === "x" && Math.abs(dx) > 6) suppressClickUntil = Date.now() + 400;
  if (dx < -90) deleteItem(kind, id, wrap);
}

$("#main").addEventListener("pointerup", endSwipe);
$("#main").addEventListener("pointercancel", endSwipe);

/* -------------------------------------------------------------- 바텀 시트 */
const sheet = $("#sheet");
const backdrop = $("#backdrop");
let sheetSubmit = null;

function closeSheet() {
  sheet.classList.remove("on");
  backdrop.classList.remove("on");
  $("#fab").classList.remove("hidden");
  sheetSubmit = null;
}

backdrop.addEventListener("click", closeSheet);

function quickRow(name, options, current) {
  return `<div class="quick" data-quick="${name}">${options
    .map(([value, label]) => `<button type="button" data-value="${value}"
      class="${String(current) === String(value) ? "on" : ""}">${label}</button>`)
    .join("")}</div>`;
}

function sheetForm(kind, item) {
  const editing = !!item;
  const today = todayISO();

  if (kind === "tasks") {
    return {
      title: editing ? "할일 수정" : "할일 추가",
      hint: "마감 시각을 넣으면 그 시간에 알림이 옵니다.",
      body: `
        <div class="field"><label>할일</label>
          <input id="f-title" placeholder="예: 분리수거 내놓기" value="${esc(item?.title || "")}" autocomplete="off"></div>
        <div class="field"><label>언제까지</label>
          ${quickRow("date", [[today, "오늘"], [shiftDays(today, 1), "내일"], [shiftDays(today, 7), "다음 주"], ["", "없음"]], item?.due_date ?? "")}
          <div class="row" style="margin-top:10px">
            <input id="f-date" type="date" value="${esc(item?.due_date || "")}">
            <input id="f-time" type="time" value="${esc(item?.due_time || "")}">
          </div></div>
        <div class="field"><label>반복</label>
          ${quickRow("repeat", [["none", "안 함"], ["daily", "매일"], ["weekly", "매주"], ["monthly", "매월"]], item?.repeat || "none")}</div>
        <div class="field"><label>담당 · 메모</label>
          <div class="row">
            <input id="f-assignee" placeholder="담당 (선택)" value="${esc(item?.assignee || "")}" autocomplete="off">
            <input id="f-note" placeholder="메모 (선택)" value="${esc(item?.note || "")}" autocomplete="off">
          </div></div>`,
      collect: () => ({
        title: $("#f-title").value.trim(),
        due_date: $("#f-date").value,
        due_time: $("#f-time").value,
        repeat: sheet.querySelector('[data-quick="repeat"] .on')?.dataset.value || "none",
        assignee: $("#f-assignee").value.trim(),
        note: $("#f-note").value.trim(),
      }),
    };
  }

  if (kind === "shopping") {
    return {
      title: editing ? "살 것 수정" : "살 것 추가",
      hint: "가족 누구나 담을 수 있어요.",
      body: `
        <div class="field"><label>품목</label>
          <input id="f-title" placeholder="예: 우유" value="${esc(item?.name || "")}" autocomplete="off"></div>
        ${editing ? "" : `<div class="field"><label>자주 사는 것</label>
          <div class="quick" data-quick="frequent">${FREQUENT
            .map((name) => `<button type="button" data-value="${name}">${name}</button>`).join("")}</div></div>`}
        <div class="field"><label>수량 · 메모</label>
          <div class="row">
            <input id="f-qty" placeholder="예: 2팩" value="${esc(item?.quantity || "")}" autocomplete="off">
            <input id="f-note" placeholder="메모 (선택)" value="${esc(item?.note || "")}" autocomplete="off">
          </div></div>
        <div class="field"><label>급한가요?</label>
          ${quickRow("urgent", [["0", "보통"], ["1", "🔥 급함"]], item?.urgent ? "1" : "0")}</div>`,
      collect: () => ({
        name: $("#f-title").value.trim(),
        quantity: $("#f-qty").value.trim(),
        note: $("#f-note").value.trim(),
        urgent: sheet.querySelector('[data-quick="urgent"] .on')?.dataset.value === "1",
      }),
    };
  }

  return {
    title: editing ? "일정 수정" : "일정 추가",
    hint: `시작 ${state.leadMinutes || 30}분 전에 미리 알려드려요.`,
    body: `
      <div class="field"><label>일정</label>
        <input id="f-title" placeholder="예: 치과 예약" value="${esc(item?.title || "")}" autocomplete="off"></div>
      <div class="field"><label>날짜</label>
        ${quickRow("date", [[today, "오늘"], [shiftDays(today, 1), "내일"], [shiftDays(today, 7), "다음 주"]], item?.date ?? "")}
        <div class="row" style="margin-top:10px">
          <input id="f-date" type="date" value="${esc(item?.date || today)}">
          <input id="f-time" type="time" value="${esc(item?.start_time || "")}">
        </div></div>
      <div class="field"><label>장소 · 메모</label>
        <div class="row">
          <input id="f-place" placeholder="장소 (선택)" value="${esc(item?.location || "")}" autocomplete="off">
          <input id="f-note" placeholder="메모 (선택)" value="${esc(item?.note || "")}" autocomplete="off">
        </div></div>`,
    collect: () => ({
      title: $("#f-title").value.trim(),
      date: $("#f-date").value || today,
      start_time: $("#f-time").value,
      location: $("#f-place").value.trim(),
      note: $("#f-note").value.trim(),
    }),
  };
}

async function openSheet(kind, id = null) {
  let item = null;
  if (id) {
    const source = { tasks: state.tasks, shopping: state.shopping, events: state.events }[kind];
    item = (source || []).find((row) => row.id === id) || findInSummary(kind, id);
  }
  const form = sheetForm(kind, item);

  sheet.innerHTML = `
    <div class="grip"></div>
    <h2>${form.title}</h2>
    <p class="hint">${esc(form.hint)}</p>
    ${form.body}
    <button class="submit" id="f-submit">${item ? "수정 저장" : "추가하기"}</button>
    ${item ? '<button class="linkbtn" id="f-delete">삭제</button>' : ""}`;

  sheet.classList.add("on");
  backdrop.classList.add("on");
  $("#fab").classList.add("hidden");
  sheet.scrollTop = 0;
  buzz();
  setTimeout(() => { if (!item) $("#f-title").focus(); }, 320);

  sheetSubmit = async () => {
    const payload = form.collect();
    if (!payload.title && !payload.name) { toast("내용을 입력해 주세요"); return; }
    if (item) {
      await api(`/api/${kind}/${item.id}`, { method: "PATCH", body: JSON.stringify(payload) });
      toast("수정했어요");
    } else {
      await api(`/api/${kind}`, { method: "POST", body: JSON.stringify(payload) });
      toast("추가했어요");
    }
    buzz([8, 30, 8]);
    closeSheet();
    refresh({ silent: true });
  };

  $("#f-submit").addEventListener("click", () => sheetSubmit && sheetSubmit());
  if (item) {
    $("#f-delete").addEventListener("click", async () => {
      closeSheet();
      const wrap = document.querySelector(`.swipe[data-kind="${kind}"][data-id="${item.id}"]`);
      if (wrap) deleteItem(kind, item.id, wrap);
      else { await api(`/api/${kind}/${item.id}`, { method: "DELETE" }); toast("삭제했어요"); refresh({ silent: true }); }
    });
  }
}

// 시트 안의 빠른 선택 칩
sheet.addEventListener("click", (event) => {
  const button = event.target.closest(".quick button");
  if (!button) return;
  const group = button.parentElement;
  const name = group.dataset.quick;

  if (name === "frequent") {
    $("#f-title").value = button.dataset.value;
    buzz();
    return;
  }
  group.querySelectorAll("button").forEach((el) => el.classList.toggle("on", el === button));
  if (name === "date") {
    const input = $("#f-date");
    if (input) input.value = button.dataset.value;
  }
  buzz();
});

// 엔터로 바로 저장
sheet.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && sheetSubmit) { event.preventDefault(); sheetSubmit(); }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closeSheet();
});

$("#fab").addEventListener("click", () => {
  openSheet(state.tab === "today" ? "tasks" : state.tab);
});

/* ---------------------------------------------------------------- 알림 버튼 */
$("#btn-notify").addEventListener("click", async () => {
  $("#bell").classList.add("ring-anim");
  setTimeout(() => $("#bell").classList.remove("ring-anim"), 720);
  buzz([10, 30, 10]);
  const result = await api("/api/notify/digest", { method: "POST" });
  toast(result.sent ? `요약 알림을 보냈어요 (${result.channel})` : "알림 실패 — 설정을 확인하세요");
});

/* ------------------------------------------------------- 당겨서 새로고침 */
let pull = null;

document.addEventListener("touchstart", (event) => {
  if (window.scrollY > 0 || sheet.classList.contains("on")) return;
  pull = { y: event.touches[0].clientY, dy: 0 };
}, { passive: true });

document.addEventListener("touchmove", (event) => {
  if (!pull) return;
  pull.dy = event.touches[0].clientY - pull.y;
  if (pull.dy <= 0) return;
  const distance = Math.min(pull.dy * 0.5, 70);
  const ptr = $("#ptr");
  ptr.style.transform = `translate(-50%, ${distance - 46}px) rotate(${distance * 4}deg)`;
  ptr.style.opacity = Math.min(distance / 50, 1);
}, { passive: true });

document.addEventListener("touchend", async () => {
  if (!pull) return;
  const ptr = $("#ptr");
  const shouldRefresh = pull.dy * 0.5 > 55;
  pull = null;
  if (shouldRefresh) {
    ptr.style.transform = "translate(-50%, 18px)";
    ptr.classList.add("spin");
    buzz(12);
    await refresh({ silent: true });
    ptr.classList.remove("spin");
    toast("최신 정보로 새로고침했어요");
  }
  ptr.style.transform = "translate(-50%, -46px)";
  ptr.style.opacity = 0;
});

/* -------------------------------------------------------------------- 시작 */
initTheme();
moveInk();
window.addEventListener("resize", moveInk);

load("today").catch(() => {
  $("#view-today").innerHTML = emptyBox("📡", "서버에 연결하지 못했어요");
});

// 화면을 다시 볼 때와 1분마다 자동 갱신 (날짜가 바뀌어도 반영)
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) refresh({ silent: true });
});
setInterval(() => { if (!document.hidden) refresh({ silent: true }); }, 60000);
