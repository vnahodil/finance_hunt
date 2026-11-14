# Development Roadmap (`finance_hunt`)
## Zurich Finance, Asset Management & Wealth Management Job Radar

Automated daily job discovery, commute calculation, and semantic scoring pipeline for finance, asset management, and wealth management roles within a **60-minute commute of Zurich / Glattbrugg / Zug / Pfäffikon SZ**.

---

## 🎯 Architecture & Non-Breaking Transition Strategy
To adapt this repository from chemistry to finance **without breaking existing functionality at any point**, changes are divided into decoupled, staged phases:
1. **Never edit Python logic before configuration**: Ground the system in `config/candidate/` and `config/targets.yaml`. The existing scrapers (`jobs.ch`, `jobspy`, `workday`, `startup_apis`) are query-driven; changing queries immediately yields finance roles without Python syntax risk.
2. **Isolate the database**: Move from `chem_jobs.db` to `finance_jobs.db` while copying the `commute_cache` table. This prevents chemistry jobs from polluting the finance dashboard while preserving SBB transit calculations.
3. **Decouple evaluation**: Update `src/models.py` and `src/evaluator.py` to recognize financial role categories, degrees, and heuristic filters.
4. **Update presentation**: Refresh `src/dashboard.py` categories and the 1-click tailored CV/cover letter prompt.
5. **Phase out domain-specific scrapers**: Bypass chemistry scrapers (Empa, ETH spin-offs, SCS, Givaudan) while routing discovery through Swiss financial portals, Workday endpoints, and fintech APIs.
6. **Rename CLI entry points**: Transition `zurich_chem_radar.py` to `zurich_finance_radar.py` while keeping a backward-compatible alias.

---

## Milestone 1: Candidate Profile & Master YAML Configuration ✅
*Goal: Ground the system in the financial candidate profile and calibrate target queries without touching Python code.*
- [x] **Candidate Profile Setup (`config/candidate/`)**:
  - [x] Ground the pipeline in candidate profile (Candidate: Senior Quantitative PM / Director, Cambridge MPhil, CFA Charterholder, perfect 170 GRE Quant, Python/R/SQL stack, multi-billion AuM track record).
  - [x] Replace `config/candidate/career_directions.txt` with target financial tracks (Tracks 1–12):
    - *Track 1*: Quantitative Portfolio Management & Systematic Strategies (Buy-Side & Hedge Funds)
    - *Track 2*: Direct Equity Selection (Fundamental & "Quantamental" Stock Picking)
    - *Track 3*: Head of Manager Selection / Multi-Manager & Fund Solutions Lead
    - *Track 4*: Head of Mandates, Multi-Asset PM & CIO Asset Allocation
    - *Track 5*: UHNW Investment Specialist / Bespoke Portfolio Counselor ("Desk CIO")
    - *Track 6*: UHNW Client Advisor / Relationship Manager (CEE Desk or International UHNW)
    - *Track 7*: Single & Multi-Family Office (SFO / MFO) CIO or Investment Director
    - *Track 8*: Swiss Pension Funds (Pensionskassen) & Public Institutional Allocators
    - *Track 9*: Insurance & Reinsurance Institutional Investments / ALM
    - *Track 10*: Private Markets Quantitative Portfolio Solutions (PE / Private Credit / Infra)
    - *Track 11*: WealthTech, AssetTech & AI/Quant Platform Leadership
    - *Track 12*: Institutional Investment Consulting & Outsourced CIO (OCIO)
- [x] **Master Target Configuration (`config/targets.yaml`)**:
  - [x] Update `aggregator_queries` with 41 financial search terms (*"Portfolio Manager Equities"*, *"Quantitative Portfolio Manager"*, *"Head of Fund Selection"*, *"UHNW Investment Specialist"*, *"Portfolio Solutions"*, etc.).
  - [x] Update `jobs_ch_queries` with 29 Swiss market queries (*"portfolio manager"*, *"aktienanalyst"*, *"portfoliomanager aktien"*, *"leiter vermögensverwaltung"*, *"anlagestrategie"*, etc.).
  - [x] Invert `filters.positive_regex` and `filters.negative_regex`:
    - **Removed** `finance`, `accountant`, `payroll`, `financial` from negative regex.
    - **Added** positive finance terms (`portfolio\s*manager|portfoliomanager|quant|systematic|equity|fund\s*select|multi-asset|asset\s*allocation|uhnw|family\s*office|cee|wealthtech|director|vp|head\s*of|pensionskasse|ocio`).
    - **Added** negative terms for unqualified or out-of-scope roles (retail branch teller, cashier, facility, bookkeeping/payroll, IT helpdesk, wet lab chemist).
  - [x] Configure 53 structured target geographic locations across 4 clusters (`zurich_core_and_suburbs`, `schwyz_gold_coast`, `zug_financial_hub`, `secondary_commutable_hubs`) and 92 driving overrides.
  - [x] Expand `institutes_and_hubs.portals` with 25 curated Swiss financial and buy-side portals (eFinancialCareers, CFA Society, Finews, Financejobs.ch, NZZ Jobs, Alpha.ch, Selby Jennings, VPS, SwissDevJobs, DataCareer).
  - [x] Verify 100% coverage across ~125 curated targets in Sectors A–H (Elite Quant Hedge Funds, Private Banks, Institutional AM, Boutiques, Private Markets/PE, Family Offices, Pension Funds, WealthTech).
  - [x] Update `notifications.dashboard_url` to `https://vnahodil.github.io/finance_hunt/`.

---

## Milestone 2: Database Isolation & Commute Cache Preservation ✅
*Goal: Create a clean database for finance roles while preserving months of cached SBB commute times.*
- [x] Update `cfg.DB_PATH` in `src/config.py` to point to `finance_jobs.db`.
- [x] Run migration script to initialize `finance_jobs.db` and copy all 89 cached commute destinations from `chem_jobs.db`.
- [x] Verify that `init_db()` in `src/database.py` creates clean `jobs` and `commute_cache` tables without throwing schema errors.
- [x] Untrack and remove legacy `chem_jobs.db` from repository storage.
- [x] Verify that `--dashboard-only` runs cleanly against an empty or freshly populated `finance_jobs.db`.

---

## Milestone 3: Models & Evaluator Calibration (Gemini + Heuristic) 🧠 ✅
*Goal: Teach Gemini and the deterministic fallback how to critically evaluate finance roles.*
- [x] **Pydantic Model Updates (`src/models.py`)**:
  - [x] Updated `JobEvaluation.role_category` allowed values: `Asset Management`, `Wealth Management`, `Investment Research`, `Risk & Quantitative`, `Corporate Finance / PE`, `Fintech & Markets`, `Operations / Compliance`, `Other`.
  - [x] Updated `degree_fit` choices for finance credentials (`MSc / CFA Suitable`, `Charterholder / CFA Level II+`, `Senior Director / PM Lead`, `Entry / Junior Analyst`, `Overqualified (MD/Partner Req)`, `Retail / Non-professional`).
  - [x] Grounded field descriptions in financial track record (Cambridge MPhil, CFA Charter, UBS GWM Director, $4B+ AuM, cvxpy/Python/R).
- [x] **Heuristic Scorer (`src/evaluator.py`)**:
  - [x] Rewrote `evaluate_job_heuristic()` eliminating chemistry rules and adding comprehensive finance domain matching.
  - [x] Added heuristic checks for Tracks 1–12, CFA/quant credentials, and hard dealbreakers (retail tellers, routine bookkeeping, IT helpdesk, facility).
- [x] **Gemini Prompt Calibration (`src/evaluator.py`)**:
  - [x] Redefined persona to "Senior Swiss Financial Hiring Auditor, Asset Management Partner, and Private Banking Recruitment Director in Zurich".
  - [x] Calibrated 1-10 scoring tiers:
    - *9-10*: Exceptional fit in target investment track (Systematic/Quant PM, Direct Equities, Head of Fund Selection, UHNW Desk CIO, SFO/MFO CIO), ideal seniority.
    - *7-8*: Strong financial match with bridgeable gaps (e.g. learning firm-specific Bloomberg/Python stack, specific asset class focus).
    - *6*: Viable baseline role in financial services / corporate finance / operations.
    - *4-5*: Misaligned financial domain (e.g. pure back-office bookkeeping, retail branch counter teller).
    - *1-3*: Disqualified (Managing Partner / Executive Director, foreign location, non-finance trades).
  - [x] Updated model cascade (`gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`, `gemini-3.8-flash`, `gemini-3.5-flash`).

---

## Milestone 4: Dashboard UI & Tailoring Prompt Adaptation 📊 ✅
*Goal: Redesign `dashboard.html` and the 1-click application prompt for finance roles.*
- [x] **UI Branding & Category Filters (`src/dashboard.py`)**:
  - [x] Updated header title to *"Zurich Finance, Asset Management & Wealth Management Job Radar"*.
  - [x] Updated `<select id="catFilter">` dropdown options to match new finance categories.
  - [x] Updated commute shortcuts for Paradeplatz, Enge, Hardbrücke, Baar, Pfäffikon SZ.
- [x] **1-Click Application Tailoring Prompt (`src/dashboard.py`)**:
  - [x] Rewrote `copyPrompt()` JavaScript function to pitch Cambridge MPhil, CFA charter, PM track record (~$160bn team AuM, $4bn+ direct funds), Python/R optimization, and generate 3 CV bullets, alignment pitch, and Swiss-style cover letter.
- [x] **Email Digest Notification (`src/notify.py`)**:
  - [x] Updated branding and header/footer text to finance radar.

---

## Milestone 5: Workday & Direct ATS Ingestion for Swiss Financial Institutions 🏦 ✅
*Goal: Ingest high-speed, zero-browser vacancies from top banks, hedge funds, and asset managers.*
- [x] Connect and verify Workday CXS endpoints in `config/targets.yaml`:
  - [x] **Julius Bär** (Zurich — Private Banking & Wealth Management)
  - [x] **Vontobel** (Zurich — Wealth Management & Asset Management)
  - [x] **BlackRock** (Zurich — Multi-Asset, Systematic & Solutions)
  - [x] **Wellington Management** (Zurich — Asset Management)
  - [x] **Invesco** (Zurich — Quantitative & ETF)
  - [x] **Morningstar** (Zurich — Manager Research & Indexes)
  - [x] **State Street (SSGA)** (Zurich — Portfolio & Systematic)
  - [x] **Citi Private Bank & ICG** (Zurich — UHNW & Investment Counseling)
  - [x] **T. Rowe Price** (Zurich — Institutional Asset Management)
- [x] Connect and verify direct ATS JSON APIs in `src/scrapers/startup_apis.py`:
  - [x] **WorldQuant** (Greenhouse — Zug/Geneva)
  - [x] **Point72** (Greenhouse — Zurich/Geneva)
  - [x] **Citadel & Citadel Securities** (Greenhouse — Zurich)
  - [x] **IMC Trading** (Greenhouse — Zug)
  - [x] **Swissblock** (Lever — Baar ZG)
  - [x] **QuantCo** (Lever — Zurich)
- [x] Verified `src/scrapers/workday.py` and `startup_apis.py` return live positions and filter strictly by `cfg.TARGET_LOCATIONS_LOWER`.

---

## Milestone 6: Specialist Portals Ingestion & Chemistry Scraper Deprecation 🚀 ✅
*Goal: Ingest roles from Swiss financial portals while deprecating legacy chemistry scrapers.*
- [x] **Deprecate / Silence Chemistry Scrapers in Orchestrator**:
  - [x] Bypassed and silenced `eth_spinoffs.py`, `institutes.py`, `myscience.py`, `lifesciencework.py`, `scs.py`, and `givaudan.py` (return clean `[]`).
  - [x] Cleaned up non-job regexes in `career_pages.py`.
- [x] **Test Jobs.ch & JobSpy Ingestion**:
  - [x] Calibrated `jobs_ch` and `jobspy_aggregator` for financial keywords across Zurich, Zug, and Schwyz cantons.
  - [x] Live query returned verified positions (e.g. MCP Switzerland / Millennium in Baar, Luzerner Kantonalbank in Luzern).

---

## Milestone 7: CLI Orchestrator, Daily Automation & Documentation ⚙️ ✅
*Goal: Rename entry points cleanly while preserving workflow automation.*
- [x] Created `zurich_finance_radar.py` as primary CLI entry point with financial descriptions, 5-stage pipeline, and flags.
- [x] Maintained `zurich_chem_radar.py` as a lightweight redirect/wrapper to `zurich_finance_radar.py` to prevent broken bash/make scripts.
- [x] Updated `Makefile` targets to use `zurich_finance_radar.py`.
- [x] Updated `run_daily.sh`:
  - [x] Fixed project directory path: `PROJECT_DIR="/Users/vnahodil/dev/finance_hunt"`.
  - [x] Updated CLI command and log messages for finance radar.
- [x] Updated `README.md` and `AGENTS.md` with finance radar guidelines, candidate background, and scoring rubric.

---

## Milestone 8: Daily Notification Digest & GitHub Pages Publication 📬 ✅
*Goal: End-to-end verification of daily automated execution, email alerts, and dashboard hosting.*
- [x] Test local dashboard generation: `.venv/bin/python zurich_finance_radar.py --dashboard-only`.
- [x] Run initial discovery crawl for finance roles and inspect calibrated scores (209 evaluated, 44 verified matches &ge; 6/10, 17 top matches &ge; 8/10).
- [x] Commit and publish to GitHub Pages (`https://vnahodil.github.io/finance_hunt/`).
- [x] Verify live dashboard on GitHub Pages.

---

## Milestone 9: Deep Financial Coverage & Target Expansion 🎯 🚀
*Goal: Eliminate blind spots across CEE German terminology, multi-strat hedge funds, Crypto Valley leaders, and Swiss pension allocators.*
- [x] **Private Banking & CEE Language Expansion (Track 6)**:
  - [x] Add German CEE variations to queries: `"osteuropa"`, `"kundenberater osteuropa"`, `"relationship manager osteuropa"`, `"private banking osteuropa"`, `"client advisor emerging europe"`.
  - [x] Add CEE private banking specialists to targets: BCGE (Zurich CEE), CBH Compagnie Bancaire Helvétique, PKB Privatbank, Coutts / NatWest Wealth.
- [x] **Multi-Strat Quant Pods & Factor Research (Track 1 & Track 2)**:
  - [x] Add elite multi-strat hedge funds: Balyasny Asset Management (BAM - Zurich), ExodusPoint, Schonfeld Strategic Advisors.
  - [x] Add dedicated quant/factor queries: `"Quantitative Risk"`, `"Factor Research"`, `"Factor Investing"`, `"Systematic Equities"`, `"Desk Quant"`.
- [x] **Crypto Valley & Digital Asset Banks (Track 11: WealthTech / Digital Assets)**:
  - [x] Add institutional digital asset managers: Sygnum Bank (Zurich), AMINA Bank (Zug), Bitcoin Suisse (Zug/Baar), 21Shares (Zurich), Crypto Finance Group (Zurich).
  - [x] Add market infrastructure: SIX Group (Zurich Hardbrücke — Swiss Stock Exchange & Index Engineering).
- [x] **Swiss Pension Allocators & Insurance Asset Owners (Track 8 & Track 9)**:
  - [x] Add missing institutional asset owners: compenswiss (AHV/IV/EO Federal Fund), Generali Switzerland (Adliswil HQ), PartnerRe (Zurich), Asga Pensionskasse, GastroSocial.
  - [x] Add institutional allocators queries: `"Leiter Kapitalanlagen"`, `"Anlagechef Pensionskasse"`, `"Sammelstiftung Portfoliomanager"`.
- [x] **Swiss EAM & Wealth Manager Portals (Track 7)**:
  - [x] Add VSV / ASG (Swiss Association of Wealth Managers / EAM job board), AMAS (Asset Management Association Switzerland), and Sphere.swiss.

---

## Milestone 10: Full Endpoint Verification & Scraper Hardening 🛡️ ✅
*Goal: Audit, verify, and harden 100% of individual targets and endpoints configured in `config/targets.yaml`.*
- [x] **Workday CXS Endpoints (9/9 Verified - 100%)**:
  - [x] Verified all 9 direct institutional endpoints: Julius Bär, Vontobel, BlackRock, Wellington Management, Invesco, Morningstar, State Street (SSGA), Citi Private Bank & ICG, T. Rowe Price.
- [x] **Direct ATS JSON APIs (11/11 Verified - 100%)**:
  - [x] Discovered and fixed `QuantCo` Lever slug (`quantco` -> `quantco-`), capturing active Quant Researcher roles.
  - [x] Added `Flow Traders` Greenhouse board (`flowtraders`).
  - [x] Added `Fireblocks` Greenhouse board (`fireblocks`).
  - [x] Verified WorldQuant, Point72, IMC Trading, Swissblock, Capco, 21Shares, Schonfeld, ExodusPoint.
  - [x] Added pan-European / remote location fallback logic in `src/scrapers/startup_apis.py`.
- [x] **Swiss Portal REST APIs (100% Verified)**:
  - [x] Verified `jobs.ch` REST API across 37 financial queries returning 280+ positions per run.
- [x] **Curated Career Pages & Specialist Portals (Hardened & Concurrent)**:
  - [x] Refactored `src/scrapers/career_pages.py` to use `ThreadPoolExecutor(max_workers=15)`, reducing full scan from ~90s to ~11s.
  - [x] Cleaned and updated 45+ company career page URLs in `config/targets.yaml` (resolving 404s, path migrations, and SSL mismatches).
  - [x] Verified specialist Swiss portal URLs (CFA Society Switzerland, Finews, VSV/ASG, NZZ Jobs, Aquila Group, Michael Page, Publicjobs, Schweizer Personalvorsorge / VVP).
- [x] **End-to-End Pipeline Verification**:
  - [x] Full pipeline verified with active Gemini Flash evaluation and duplicate/commute filters.
  - [x] Total database now holds 231 evaluated roles, 47 verified matches (>=6/10), and 17 top matches (>=8/10).

