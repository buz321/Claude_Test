/* ============================================================
   HomeReach — Mortgage Affordability Calculator (UK / US)
   ============================================================ */

// ---------- Region data (indicative average prices) ----------
// UK links open Zoopla, US links open Realtor.com, both with the
// user's computed price range pre-filtered.
const REGIONS = {
  uk: [
    { name: "London",     slug: "london",              avg: 530000 },
    { name: "Manchester", slug: "manchester",          avg: 250000 },
    { name: "Birmingham", slug: "birmingham",          avg: 235000 },
    { name: "Leeds",      slug: "leeds",               avg: 240000 },
    { name: "Liverpool",  slug: "liverpool",           avg: 180000 },
    { name: "Bristol",    slug: "bristol",             avg: 350000 },
    { name: "Edinburgh",  slug: "edinburgh",           avg: 335000 },
    { name: "Glasgow",    slug: "glasgow",             avg: 175000 },
    { name: "Cardiff",    slug: "cardiff",             avg: 265000 },
    { name: "Newcastle",  slug: "newcastle-upon-tyne", avg: 200000 },
    { name: "Sheffield",  slug: "sheffield",           avg: 215000 },
    { name: "Nottingham", slug: "nottingham",          avg: 220000 },
  ],
  us: [
    { name: "New York, NY",    slug: "New-York_NY",    avg: 760000 },
    { name: "Los Angeles, CA", slug: "Los-Angeles_CA", avg: 950000 },
    { name: "Chicago, IL",     slug: "Chicago_IL",     avg: 360000 },
    { name: "Houston, TX",     slug: "Houston_TX",     avg: 340000 },
    { name: "Phoenix, AZ",     slug: "Phoenix_AZ",     avg: 450000 },
    { name: "Austin, TX",      slug: "Austin_TX",      avg: 540000 },
    { name: "Dallas, TX",      slug: "Dallas_TX",      avg: 420000 },
    { name: "Miami, FL",       slug: "Miami_FL",       avg: 560000 },
    { name: "Seattle, WA",     slug: "Seattle_WA",     avg: 850000 },
    { name: "Denver, CO",      slug: "Denver_CO",      avg: 580000 },
    { name: "Atlanta, GA",     slug: "Atlanta_GA",     avg: 400000 },
    { name: "Boston, MA",      slug: "Boston_MA",      avg: 780000 },
  ],
};

const COUNTRY_META = {
  uk: {
    symbol: "£",
    locale: "en-GB",
    currency: "GBP",
    depositLabel: "Deposit",
    defaultRate: 4.5,
    portal: "Zoopla",
    listingsUrl: (slug, min, max) =>
      `https://www.zoopla.co.uk/for-sale/property/${slug}/?price_min=${min}&price_max=${max}`,
  },
  us: {
    symbol: "$",
    locale: "en-US",
    currency: "USD",
    depositLabel: "Down payment",
    defaultRate: 6.5,
    portal: "Realtor.com",
    listingsUrl: (slug, min, max) =>
      `https://www.realtor.com/realestateandhomes-search/${slug}/price-${min}-${max}`,
  },
};

// ---------- State ----------
let country = "uk";

// ---------- Elements ----------
const $ = (sel) => document.querySelector(sel);
const els = {
  toggleBtns: document.querySelectorAll(".toggle-btn"),
  income: $("#income"),
  deposit: $("#deposit"),
  debts: $("#debts"),
  multiple: $("#multiple"),
  multipleValue: $("#multiple-value"),
  dti: $("#dti"),
  dtiValue: $("#dti-value"),
  rate: $("#rate"),
  rateValue: $("#rate-value"),
  term: $("#term"),
  termValue: $("#term-value"),
  resultPrice: $("#result-price"),
  resultLoan: $("#result-loan"),
  resultMonthly: $("#result-monthly"),
  resultLtv: $("#result-ltv"),
  resultRatio: $("#result-ratio"),
  ratioLabel: $("#ratio-label"),
  resultNote: $("#result-note"),
  ltvFill: $("#ltv-fill"),
  depositLabels: document.querySelectorAll(".deposit-label"),
  currencySymbols: document.querySelectorAll(".currency-symbol"),
  ukOnly: document.querySelectorAll(".uk-only"),
  usOnly: document.querySelectorAll(".us-only"),
  regionSelect: $("#region-select"),
  regionName: $("#region-name"),
  regionAvg: $("#region-avg"),
  regionBudget: $("#region-budget"),
  regionBadge: $("#region-badge"),
  compareFill: $("#compare-fill"),
  compareMarker: $("#compare-marker"),
  comparePct: $("#compare-pct"),
  browseBtn: $("#browse-btn"),
  ctaRange: $("#cta-range"),
  browseNote: $("#browse-note"),
};

// ---------- Helpers ----------
function fmtMoney(value) {
  const meta = COUNTRY_META[country];
  return new Intl.NumberFormat(meta.locale, {
    style: "currency",
    currency: meta.currency,
    maximumFractionDigits: 0,
  }).format(Math.max(0, Math.round(value)));
}

function parseMoneyInput(el) {
  const n = parseFloat(el.value.replace(/[^0-9.]/g, ""));
  return Number.isFinite(n) ? n : 0;
}

function formatMoneyInput(el) {
  const n = parseMoneyInput(el);
  el.value = n ? n.toLocaleString("en-US") : "0";
}

function roundTo(value, step) {
  return Math.round(value / step) * step;
}

// Monthly payment for a loan (standard amortization).
function monthlyPayment(principal, annualRatePct, years) {
  const r = annualRatePct / 100 / 12;
  const n = years * 12;
  if (principal <= 0 || n <= 0) return 0;
  if (r === 0) return principal / n;
  return (principal * r * Math.pow(1 + r, n)) / (Math.pow(1 + r, n) - 1);
}

// Loan principal affordable for a given monthly payment (inverse of above).
function principalFromPayment(payment, annualRatePct, years) {
  const r = annualRatePct / 100 / 12;
  const n = years * 12;
  if (payment <= 0 || n <= 0) return 0;
  if (r === 0) return payment * n;
  return (payment * (Math.pow(1 + r, n) - 1)) / (r * Math.pow(1 + r, n));
}

// ---------- Core calculation ----------
function calculate() {
  const income = parseMoneyInput(els.income);
  const deposit = parseMoneyInput(els.deposit);
  const rate = parseFloat(els.rate.value);
  const term = parseInt(els.term.value, 10);

  let loan, monthly, ratioText, note;

  if (country === "uk") {
    // UK: lenders cap borrowing at a multiple of gross annual income.
    const multiple = parseFloat(els.multiple.value);
    loan = income * multiple;
    monthly = monthlyPayment(loan, rate, term);
    ratioText = `${multiple}×`;
    note = `Based on a ${multiple}× income multiple — typical for UK lenders.`;
  } else {
    // US: lenders cap the monthly payment at a share of gross monthly
    // income (DTI), minus existing debt payments.
    const dti = parseFloat(els.dti.value);
    const debts = parseMoneyInput(els.debts);
    const budget = Math.max(0, (income / 12) * (dti / 100) - debts);
    loan = principalFromPayment(budget, rate, term);
    monthly = budget;
    ratioText = `${dti}%`;
    note = `Based on a ${dti}% debt-to-income ratio. Excludes property taxes, insurance, and HOA fees.`;
  }

  const price = loan + deposit;
  const ltv = price > 0 ? (loan / price) * 100 : 0;

  els.resultPrice.textContent = fmtMoney(price);
  els.resultLoan.textContent = fmtMoney(loan);
  els.resultMonthly.textContent = `${fmtMoney(monthly)}/mo`;
  els.resultLtv.textContent = `${ltv.toFixed(0)}%`;
  els.resultRatio.textContent = ratioText;
  els.resultNote.textContent = note;
  els.ltvFill.style.width = `${Math.min(100, ltv).toFixed(1)}%`;

  updateRegion(price);
}

// ---------- Region comparison + listings link ----------
function updateRegion(maxPrice) {
  const meta = COUNTRY_META[country];
  const region = REGIONS[country][els.regionSelect.selectedIndex] || REGIONS[country][0];

  els.regionName.textContent = region.name;
  els.regionAvg.textContent = fmtMoney(region.avg);
  els.regionBudget.textContent = fmtMoney(maxPrice);

  // Verdict badge
  const ratio = region.avg > 0 ? maxPrice / region.avg : 0;
  let badgeClass, badgeText;
  if (ratio >= 1) {
    badgeClass = "ok";
    badgeText = "Within budget";
  } else if (ratio >= 0.85) {
    badgeClass = "close";
    badgeText = "A stretch";
  } else {
    badgeClass = "over";
    badgeText = "Above budget";
  }
  els.regionBadge.className = `badge ${badgeClass}`;
  els.regionBadge.textContent = badgeText;

  // Budget-vs-average bar: scale so the average sits at 80% of the track.
  const markerPos = 80;
  const fillPct = Math.min(100, ratio * markerPos);
  els.compareFill.style.width = `${fillPct.toFixed(1)}%`;
  els.compareMarker.style.left = `${markerPos}%`;
  els.comparePct.textContent = `${Math.round(ratio * 100)}% of average`;

  // Listings deep link with the user's price band pre-filtered.
  const step = country === "uk" ? 5000 : 10000;
  const max = Math.max(step, roundTo(maxPrice, step));
  const min = Math.max(0, roundTo(maxPrice * 0.5, step));
  els.browseBtn.href = meta.listingsUrl(region.slug, min, max);
  els.ctaRange.textContent = `${fmtMoney(min)} – ${fmtMoney(max)}`;
  els.browseNote.textContent = `Opens ${meta.portal} with your price range pre-filtered.`;
}

// ---------- Country switching ----------
function setCountry(next) {
  country = next;
  const meta = COUNTRY_META[country];

  els.toggleBtns.forEach((btn) => {
    const active = btn.dataset.country === country;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", String(active));
  });

  els.ukOnly.forEach((el) => (el.hidden = country !== "uk"));
  els.usOnly.forEach((el) => (el.hidden = country !== "us"));
  els.currencySymbols.forEach((el) => (el.textContent = meta.symbol));
  els.depositLabels.forEach((el) => (el.textContent = meta.depositLabel));
  els.ratioLabel.textContent = country === "uk" ? "Income multiple" : "DTI used";

  els.rate.value = meta.defaultRate;
  els.rateValue.textContent = `${meta.defaultRate}%`;

  populateRegions();
  calculate();
}

function populateRegions() {
  els.regionSelect.innerHTML = "";
  REGIONS[country].forEach((r, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = r.name;
    els.regionSelect.appendChild(opt);
  });
}

// ---------- Events ----------
els.toggleBtns.forEach((btn) =>
  btn.addEventListener("click", () => setCountry(btn.dataset.country))
);

[els.income, els.deposit, els.debts].forEach((el) => {
  el.addEventListener("input", calculate);
  el.addEventListener("blur", () => {
    formatMoneyInput(el);
    calculate();
  });
});

els.multiple.addEventListener("input", () => {
  els.multipleValue.textContent = `${els.multiple.value}×`;
  calculate();
});
els.dti.addEventListener("input", () => {
  els.dtiValue.textContent = `${els.dti.value}%`;
  calculate();
});
els.rate.addEventListener("input", () => {
  els.rateValue.textContent = `${els.rate.value}%`;
  calculate();
});
els.term.addEventListener("input", () => {
  els.termValue.textContent = `${els.term.value} yrs`;
  calculate();
});
els.regionSelect.addEventListener("change", calculate);

// ---------- Init ----------
setCountry("uk");
