# Project: Zurich Finance, Asset Management & Wealth Management Job Radar

## Overview
`zurich_finance_radar` is an automated daily job discovery, commute calculation, and semantic scoring pipeline written in Python. It finds relevant Asset Management, Wealth Management, Quantitative, and Investment Research roles within a **60-minute commute of Glattbrugg / Zurich / Zug / Pfäffikon SZ**, deduplicates them in SQLite (`finance_jobs.db`), scores them via Gemini 2.5 Flash (or a deterministic financial fallback), and renders a zero-dependency interactive HTML tracker (`dashboard.html`).

Core entry point: `zurich_finance_radar.py` (with backward-compatible alias `zurich_chem_radar.py`)
Development backlog: [Roadmap](ROADMAP.md)

---

## Candidate Profile Context (Ground Truth for Scoring & Filtering)
Every scraper filter, keyword regex, and LLM prompt MUST align with this exact candidate profile:
- **Candidate:** Senior Quantitative Portfolio Manager & Investment Director
- **Education & Credentials:** MPhil in Finance & Economics (University of Cambridge, top 20%, Grade 68) & BSc in Economics (Charles University, with Honors) + CFA Charterholder + GRE Quantitative 170/170 (94th percentile).
- **Recent Experience:** Director & Quantitative Portfolio Manager at **UBS Global Wealth Management** (Zurich). Managed $4B+ across single-name equity mandates, multi-asset solutions, and fund-of-funds within a $160B AuM mandates business. Direct fundamental equity selection rotation, multi-manager due diligence, and bespoke UHNW advisory.
- **Effective Experience Level:** ~7+ years of institutional portfolio management, quantitative modeling, and investment advisory experience (Director / Senior PM level).
- **Target Financial Tracks (1–12):**
  - *Track 1:* Quantitative Portfolio Management & Systematic Strategies (Buy-Side & Hedge Funds: QRT, Millennium, Man AHL, Citadel, Point72, Swisscanto, Vontobel Vescore, Finreon)
  - *Track 2:* Direct Equity Selection (Fundamental & Quantamental Stock Picking)
  - *Track 3:* Head of Manager Selection / Multi-Manager & Fund Solutions Lead
  - *Track 4:* Head of Mandates, Multi-Asset PM & CIO Asset Allocation
  - *Track 5:* UHNW Investment Specialist / Bespoke Portfolio Counselor ("Desk CIO")
  - *Track 6:* UHNW Client Advisor / Relationship Manager (CEE Desk or International UHNW)
  - *Track 7:* Single & Multi-Family Office (SFO / MFO) CIO or Investment Director
  - *Track 8:* Swiss Pension Funds (Pensionskassen) & Public Institutional Allocators (BVK, Compenswiss, Publica)
  - *Track 9:* Insurance & Reinsurance Institutional Investments / ALM (Swiss Re, Zurich Insurance)
  - *Track 10:* Private Markets Quantitative Portfolio Solutions (Partners Group, LGT Capital Partners)
  - *Track 11:* WealthTech, AssetTech & AI/Quant Platform Leadership (Sygnum, AMINA, Swissquote, SIX Group)
  - *Track 12:* Institutional Investment Consulting & Outsourced CIO (OCIO) (Mercer, Cambridge Associates)
- **Target Titles:** Director, Vice President, Senior Portfolio Manager, Quantitative Portfolio Manager, Quantitative Researcher, Alpha Researcher, Head of Fund Selection, Equity Analyst, Multi-Asset Portfolio Manager, Investment Specialist, Desk CIO, Family Office CIO.
- **Qualification Nuance:**
  - **INCLUDE:** Senior Director / PM roles, CFA charterholder roles, quantitative finance/econometrics roles, and buy-side research positions.
  - **EXCLUDE:** Retail branch tellers (*Schaltermitarbeiter*), clerks, bookkeeping/payroll (*Buchhaltung*), IT helpdesk, facility maintenance, junior undergraduate apprenticeships (*KV-Lehrstelle*), Managing Partners demanding 20+ years of executive ownership, or wet lab scientific roles.
- **Languages:** English (C2 Native/Bilingual, Cambridge CPE Grade A), German (Conversational B1/B2, reading Swiss documentation & investment publications), Czech (Native). Exclude roles explicitly requiring native/C2 German for domestic retail client advisory.
- **Commute Constraint:** Base is **Glattbrugg / Zurich North**. Maximum door-to-door commute is **60 minutes** via public transit (SBB API `transport.opendata.ch` for 08:00 arrival) OR car (`DRIVING_OVERRIDES` for Zurich financial centers: Paradeplatz, Enge, Altstetten, Oerlikon, Lake Zurich Gold/Silver Coast, Schwyz Hedge Fund corridor: Pfäffikon SZ, Wollerau, Freienbach, Zug/Baar low-tax financial hub). Basel SBB roles (~60 min IC train) are included if hybrid or near the station.

---

## Antigravity Agent Workflow Guidelines
1. **Environment Execution:** Always run Python commands inside `.venv/bin/python` or via `make` targets.
2. **Using Subagents:**
   - When adding a new scraper for a JavaScript-rendered Swiss job board (e.g., `efinancialcareers.ch`, `jobs.ch`, or company career pages), use the **browser subagent (`/browser`)** to inspect the DOM or network XHR requests before writing `BeautifulSoup` or JSON-API code.
   - When modifying the HTML template in `generate_html_dashboard()`, verify layout and `localStorage` filtering in `/browser`.
3. **Database Safety:** Never delete `finance_jobs.db`—it holds historical seen-job hashes (`jobs`) and the SBB commute cache (`commute_cache`). Use `ALTER TABLE` migrations if adding columns.
