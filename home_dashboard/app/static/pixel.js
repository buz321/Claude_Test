"use strict";

/* =========================================================================
 * 도트 그래픽 — 캐릭터(나비)와 완료 이펙트
 * 이미지 파일 없이 픽셀 배열을 캔버스에 찍습니다.
 * ========================================================================= */

window.Pixel = (function () {
  const PALETTE = {
    o: "#5a3a26",   // 외곽선
    b: "#e08a52",   // 몸통
    l: "#fbe7d4",   // 배 (밝은 털)
    e: "#2b1a12",   // 눈
    p: "#d1707f",   // 코
    z: "#a8927f",   // 잠잘 때 Z
  };

  // 16 × 16 기본 자세
  const BASE = [
    "................",
    "..oo........oo..",
    "..obo......obo..",
    "..obbo....obbo..",
    "..obbboooobbbo..",
    "..obbbbbbbbbbo..",
    ".obbbbbbbbbbbbo.",
    ".obbeebbbbeebbo.",
    ".obbeebbbbeebbo.",
    ".obbbbbppbbbbbo.",
    ".obbbbbbbbbbbbo.",
    ".obblllllllllbo.",
    ".obblllllllllbo.",
    "..obllllllllbo..",
    "..oobbbbbbbboo..",
    "....oooooooo....",
  ];

  /** 눈 부분(7·8행)만 갈아끼워 표정을 만듭니다. */
  function withEyes(row7, row8) {
    return BASE.map((row, i) => (i === 7 ? row7 : i === 8 ? row8 : row));
  }

  const MOODS = {
    idle:  BASE,
    blink: withEyes(".obboobbbboobbo.", ".obbbbbbbbbbbbo."),
    happy: withEyes(".obbebbbbbbebbo.", ".obebebbbbebebo."),   // 눈웃음 ^ ^
    sad:   withEyes(".obebebbbbebebo.", ".obbebbbbbbebbo."),   // 처진 눈
    sleep: withEyes(".obboobbbboobbo.", ".obbbbbbbbbbbbo."),
  };

  const Z_SPRITE = ["..z.", ".z..", "zzz.", "...."];

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function paint(ctx, rows, scale, offsetX, offsetY) {
    rows.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const ch = row[x];
        if (ch === ".") continue;
        ctx.fillStyle = PALETTE[ch];
        ctx.fillRect(offsetX + x * scale, offsetY + y * scale, scale, scale);
      }
    });
  }

  /* --------------------------------------------------------------- 캐릭터 */
  const pets = [];
  let looping = false;

  function loop(now) {
    // 화면에서 사라진 캔버스는 정리 (다시 그릴 때마다 새로 붙기 때문)
    for (let i = pets.length - 1; i >= 0; i--) {
      if (!pets[i].canvas.isConnected) pets.splice(i, 1);
    }
    if (!pets.length) { looping = false; return; }

    pets.forEach((pet) => {
      const t = now - pet.born;
      let mood = pet.mood;

      // 3~6초마다 한 번씩 눈을 깜빡입니다.
      if (mood === "idle" && !reduceMotion) {
        if (now > pet.nextBlink) {
          if (now < pet.nextBlink + 160) mood = "blink";
          else pet.nextBlink = now + 3000 + Math.random() * 3000;
        }
      }
      // 완료 축하는 잠깐만 유지하고 원래 기분으로 돌아갑니다.
      if (pet.cheerUntil && now < pet.cheerUntil) mood = "happy";

      // 숨 쉬듯 1픽셀 위아래 (기쁠 때는 살짝 점프)
      let bob = 0;
      if (!reduceMotion) {
        const cheering = pet.cheerUntil && now < pet.cheerUntil;
        bob = cheering
          ? -Math.round(Math.abs(Math.sin(t / 90)) * 3)
          : Math.round((Math.sin(t / 900) + 1) / 2);
      }

      const s = pet.scale;
      const ctx = pet.ctx;
      ctx.clearRect(0, 0, pet.canvas.width, pet.canvas.height);
      paint(ctx, MOODS[mood] || BASE, s, 0, (bob + 1) * s);

      if (pet.mood === "sleep") {
        const float = reduceMotion ? 0 : Math.round((now / 500) % 3);
        paint(ctx, Z_SPRITE, s, 13 * s, (2 - float) * s);
      }
    });
    requestAnimationFrame(loop);
  }

  /**
   * 캐릭터를 붙입니다.
   * @param {HTMLElement} host  캔버스를 넣을 요소
   * @param {number} scale      픽셀 하나의 크기(px)
   */
  function mountPet(host, scale) {
    if (!host) return null;
    const canvas = document.createElement("canvas");
    canvas.width = 16 * scale;
    canvas.height = (16 + 2) * scale;          // 위아래로 움직일 여유
    canvas.style.width = `${16 * scale}px`;
    canvas.style.height = `${(16 + 2) * scale}px`;
    canvas.style.imageRendering = "pixelated";
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "우리집 고양이 나비");
    host.appendChild(canvas);

    const pet = {
      canvas,
      ctx: canvas.getContext("2d"),
      scale,
      mood: "idle",
      born: performance.now(),
      nextBlink: performance.now() + 2000,
      cheerUntil: 0,
    };
    pets.push(pet);
    if (!looping) { looping = true; requestAnimationFrame(loop); }
    return pet;
  }

  /** 모든 캐릭터의 기분을 바꿉니다. idle | happy | sad | sleep */
  function setMood(mood) {
    pets.forEach((pet) => { pet.mood = mood; });
  }

  /** 잠깐 기뻐하기 (할일을 끝냈을 때) */
  function cheer(ms = 2200) {
    const until = performance.now() + ms;
    pets.forEach((pet) => { pet.cheerUntil = until; });
  }

  /* ------------------------------------------------------------- 완료 이펙트 */
  function confettiColors() {
    const style = getComputedStyle(document.documentElement);
    return ["--accent", "--warn", "--ok", "--danger"]
      .map((name) => style.getPropertyValue(name).trim() || "#c2622d");
  }

  /** 요소 위치에서 도트 색종이가 튀어오릅니다. */
  function celebrate(element) {
    if (reduceMotion || !element) return;
    const rect = element.getBoundingClientRect();
    const colors = confettiColors();
    const canvas = document.createElement("canvas");
    canvas.className = "confetti";
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");

    const size = 4;
    const bits = Array.from({ length: 16 }, () => ({
      x: rect.left + rect.width / 2,
      y: rect.top + rect.height / 2,
      vx: (Math.random() - 0.5) * 5,
      vy: -2.5 - Math.random() * 3.5,
      color: colors[Math.floor(Math.random() * colors.length)],
    }));

    const start = performance.now();
    (function step(now) {
      const elapsed = now - start;
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      bits.forEach((bit) => {
        bit.vy += 0.22;               // 중력
        bit.x += bit.vx;
        bit.y += bit.vy;
        ctx.globalAlpha = Math.max(0, 1 - elapsed / 900);
        ctx.fillStyle = bit.color;
        // 도트 느낌을 위해 좌표를 격자에 맞춥니다.
        ctx.fillRect(Math.round(bit.x / size) * size, Math.round(bit.y / size) * size, size, size);
      });
      if (elapsed < 900) requestAnimationFrame(step);
      else canvas.remove();
    })(start);
  }

  return { mountPet, setMood, cheer, celebrate, reduceMotion };
})();
