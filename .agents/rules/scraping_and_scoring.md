---
trigger: always_on
description: Architectural invariants, SDK rules, and anti-blocking constraints for zurich_finance_radar
---

# Mandatory Engineering Constraints

1. **Google GenAI SDK (`google-genai` only):**
   - Always use `from google import genai` and `client.models.generate_content(...)`.
   - NEVER import the deprecated `google.generativeai` package.
   - Always maintain `evaluate_job_heuristic()` as a zero-API-key fallback whenever `GEMINI_API_KEY` is unset or raises a quota/network error.

2. **JobSpy Installation & Rate-Limiting:**
   - `python-jobspy` must be installed from `git+https://github.com/speedyapply/JobSpy.git` (not PyPI) to retain 2026 LinkedIn/Indeed parser fixes.
   - To prevent residential IP blocks on LinkedIn, never set `results_wanted` above `35` per query or `hours_old` above `72` on automated daily runs.

3. **Swiss Financial Portals & Workday CXS Endpoints:**
   - Query Workday endpoints via direct CXS REST endpoints (e.g. `vontobel/Vontobel_External_Career`, `juliusbaer/External`).
   - Query Swiss fintechs and hedge funds via structured Greenhouse (`boards-api.greenhouse.io/v1/boards/{slug}/jobs`) and Lever (`api.lever.co/v0/postings/{slug}`) JSON APIs.
   - Query `jobs.ch` via native REST endpoint `https://www.jobs.ch/api/v1/public/search` (capped at max 20 rows per query to prevent 422 errors).

4. **SBB API Etiquette (`transport.opendata.ch`):**
   - Always check `DRIVING_OVERRIDES` first, then the SQLite `commute_cache` table, before making an HTTP GET to `http://transport.opendata.ch/v1/connections`.
   - Never make uncached SBB API calls inside tight loops without caching the normalized city name.

5. **Dashboard Self-Containment:**
   - `dashboard.html` must remain a single, zero-server HTML file using vanilla CSS/JS and `localStorage` (`appliedJobs`, `hiddenJobs`) so it can be opened directly via `file://`.