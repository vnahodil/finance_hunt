# 🏦 Zurich Finance, Asset Management & Wealth Management Job Radar

Automated daily job discovery, SBB/car commute calculation, and semantic profile-fit evaluation pipeline for **Asset Management, Quantitative Strategies, Wealth Management, and Investment Research** roles within a **60-minute commute of Zurich / Glattbrugg / Zug / Baar / Pfäffikon SZ**.

---

## 🎯 Target Profile
Tailored for: **Candidate (Senior Quantitative PM / Director)**
- **Education & Credentials:** MPhil in Finance & Economics, CFA Charterholder, GRE Quant 170/170.
- **Track Record:** Senior institutional Portfolio Manager & Director with multi-billion-dollar portfolio management track record ($4B+ direct PM across single-name equity mandates, multi-asset solutions, and fund-of-funds). Direct fundamental equity selection, multi-manager due diligence, and bespoke UHNW advisory.
- **Quantitative & Technical Edge:** Python (`cvxpy`, ECOS convex optimization, pandas, numpy, scikit-learn), R, SQL, Git, Bloomberg, FactSet, Morningstar Direct.

---

## 🚀 Target Financial Tracks (1–12)
1. **Quantitative Portfolio Management & Systematic Strategies** (Hedge funds, systematic buy-side: QRT, Millennium, Man AHL, Citadel, Point72, Swisscanto, Vontobel Vescore, Finreon)
2. **Direct Equity Selection** (Fundamental & Quantamental stock picking for active equity funds)
3. **Head of Manager Selection / Multi-Manager & Fund Solutions** (Leading open-architecture fund selection)
4. **Head of Mandates, Multi-Asset PM & CIO Asset Allocation** (Multi-asset investment mandates & tactical asset allocation)
5. **UHNW Investment Specialist / Bespoke Portfolio Counselor** ("Desk CIO" for tier-1 private banks)
6. **UHNW Client Advisor / Relationship Manager** (CEE Desk & International UHNW)
7. **Single & Multi-Family Office (SFO / MFO) CIO or Investment Director**
8. **Swiss Pension Funds (Pensionskassen) & Public Institutional Allocators** (BVK, Compenswiss, Publica)
9. **Insurance & Reinsurance Institutional Investments / ALM** (Swiss Re, Zurich Insurance)
10. **Private Markets Quantitative Portfolio Solutions** (Partners Group, LGT Capital Partners)
11. **WealthTech, AssetTech & AI/Quant Platform Leadership** (Sygnum, AMINA, Swissquote, SIX Group)
12. **Institutional Investment Consulting & Outsourced CIO (OCIO)** (Mercer, Cambridge Associates)

---

## 🛠️ Multi-Tier Financial Ingestion Architecture
1. **Aggregators (JobSpy):** Scrapes Indeed Switzerland, LinkedIn, and Google Jobs with 40+ tailored financial queries.
2. **Workday CXS REST APIs:** Direct high-speed JSON queries for tier-1 institutions without headless browsers:
   - **Partners Group** (Baar)
   - **Julius Bär** (Zurich)
   - **Vontobel** (Zurich)
   - **Swiss Re** (Zurich)
   - **Zurich Insurance Group** (Zurich)
   - **Pictet** (Zurich / Geneva)
   - **LGT Capital Partners** (Pfäffikon SZ)
3. **Direct Fintech & Digital Asset APIs:** Greenhouse, Lever, and REST endpoints for Swiss fintechs (WorldQuant, IMC, Swissblock, Sygnum, etc.).
4. **Curated Financial Career Pages:** Monitors elite hedge funds, private banks, multi-family offices, and pension allocators.
5. **jobs.ch REST API:** Full query sweep across Swiss cantons (Zurich, Zug, Schwyz, Basel, Bern, Lucerne).
6. **Smart Commute Engine:** SBB OpenData API (`transport.opendata.ch`) for `08:00` arrival from Glattbrugg + 92 pre-computed driving overrides for financial hubs (Paradeplatz, Baar, Pfäffikon SZ, Wollerau, etc.).
7. **Semantic Scoring:** Gemini 2.5 Flash via `google-genai` SDK with deterministic heuristic fallback.
8. **Zero-Server Dashboard & GitHub Pages:** Self-contained `dashboard.html` with 1-click tailored application prompts and `localStorage` tracking.

---

## 💻 Quick Start

### 1. Setup Environment
```bash
cp .env.example .env
# Set your Gemini API key in .env:
# export GEMINI_API_KEY="AIza..."
```

### 2. Run Discovery & Publish
```bash
# Full daily run & auto-publish to GitHub Pages:
make run

# Fast run (skipping slow aggregator pagination) & publish:
make fast

# Re-render dashboard from existing SQLite database & publish:
make publish

# Re-render dashboard locally without publishing:
make dashboard
```

### 3. Daily Automation & Email Alerts (16:00 / 4:00 PM)
Automated every day at **16:00 (4:00 PM)** via native macOS `launchd`:
```bash
# Check status of scheduled daily agent:
make status-schedule

# Reload schedule if modified:
make schedule

# Test email digest delivery immediately:
make test-email
```

### 4. Live Dashboard URL
The dashboard is published via GitHub Pages at:
👉 **`https://vnahodil.github.io/finance_hunt/`**

Status markers (`Applied`, `Hidden`), category filters, and search query state are persistently saved in your browser's `localStorage`.
