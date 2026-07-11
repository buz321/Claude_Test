# HomeReach — Mortgage Affordability Calculator

A modern, single-page web app that estimates how much you can borrow and what
price of home you can afford, for the **UK** and **US**.

## Features

- **Country toggle (UK / US)** — switches currency, lending model, and regions.
- **UK model** — borrowing capped at an income multiple (3.5×–5.5×, default 4.5×),
  the way UK lenders actually assess affordability.
- **US model** — borrowing derived from a debt-to-income ratio (28%–43%, default 36%):
  your affordable monthly payment is converted into a loan amount using standard
  amortization at your chosen rate and term.
- **Live results** — maximum property price, borrowing power, monthly payment,
  and loan-to-value, updated as you type.
- **Homes within reach** — pick a city/region to compare your budget against the
  local average price, then jump straight to real listings on
  **Zoopla** (UK) or **Realtor.com** (US) with your price range pre-filtered.

## Running

No build step — it's plain HTML/CSS/JS:

```bash
cd mortgage-calculator
python3 -m http.server 8000
# open http://localhost:8000
```

Or just open `index.html` in a browser.

## Notes

- Estimates only — not financial advice.
- US figures exclude property taxes, homeowners insurance, and HOA fees.
- Area average prices are indicative, hardcoded in `app.js` (`REGIONS`);
  swapping in a live data source only requires changing that table.
