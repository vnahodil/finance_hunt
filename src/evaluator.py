"""Gemini Flash semantic evaluator + zero-cost heuristic fallback."""

import re
import time
import sqlite3
from typing import Optional

from src.config import cfg
from src.models import JobEvaluation
from src.scrapers.description_fetcher import fetch_job_description_body


# ---------------------------------------------------------------------------
# Heuristic (deterministic, zero-API-key) fallback scorer
# ---------------------------------------------------------------------------

def evaluate_job_heuristic(title: str, company: str, desc: str, source: str, location: str = "") -> JobEvaluation:
    """Zero-cost deterministic scorer calibrated for financial, asset management, and quantitative roles."""
    text = f"{title} {company} {desc or ''}".lower()
    t_clean = (title or "").strip()
    loc_clean = (location or "").strip()
    d_clean = (desc or "").strip()
    t_lower = t_clean.lower()

    # 0. Foreign locations (Boston, USA, Frankfurt, London, etc.) - check title and location ONLY
    if cfg.FOREIGN_LOCATIONS_REGEX.search(t_clean) or cfg.FOREIGN_LOCATIONS_REGEX.search(loc_clean):
        return JobEvaluation(
            is_relevant=False, match_score=1, role_category="Other",
            degree_fit="Foreign Location", language_req="N/A",
            track_alignment="Disqualified: Outside Switzerland",
            fit_strengths="None",
            career_gaps="Position is located outside Switzerland.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: None | ⚠️ Gaps: Position located outside Switzerland.",
            scorer="heuristic",
        )

    # 1. Hard exclusions: Negative keywords (teller, cashier, clerk, payroll, receptionist, trades, facility)
    if cfg.NEGATIVE_ROLE_KEYWORDS.search(t_clean):
        return JobEvaluation(
            is_relevant=False, match_score=1, role_category="Other",
            degree_fit="Disqualified Title", language_req="N/A",
            track_alignment="Disqualified: Non-target track",
            fit_strengths="None",
            career_gaps="Retail branch, bookkeeping, clerical, facility, or non-target title.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: None | ⚠️ Gaps: Disqualified clerical, retail, or non-finance title.",
            scorer="heuristic",
        )

    # 2. Hard exclusions: Academic Postdocs, Professorships, Apprenticeships, Trades
    if any(k in t_lower for k in ["postdoc", "postdoctoral", "professorship", "professor"]):
        return JobEvaluation(
            is_relevant=False, match_score=2, role_category="Other",
            degree_fit="Retail / Non-professional", language_req="N/A",
            track_alignment="Disqualified: Academic Postdoc",
            fit_strengths="Research overlap.",
            career_gaps="Demands completed PhD for academic research/teaching track.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: Research background | ⚠️ Gaps: Postdoctoral position requires academic track.",
            scorer="heuristic",
        )
    if any(k in t_lower for k in ["lehrstelle", "schnupper", "lernende", "kv-lehrstelle", "berufslehre"]):
        return JobEvaluation(
            is_relevant=False, match_score=1, role_category="Other",
            degree_fit="Retail / Non-professional", language_req="N/A",
            track_alignment="Disqualified: Vocational Apprenticeship",
            fit_strengths="Under-leveled for Director / Portfolio Manager.",
            career_gaps="Apprenticeship / vocational position.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: Under-leveled | ⚠️ Gaps: Apprenticeship / vocational training.",
            scorer="heuristic",
        )
    if any(k in t_lower for k in [
        "electrical engineer", "mechanical engineer", "civil engineer", "chemist", "chemielaborant",
        "laboratory technician", "wet lab", "arzt", "pflegefachkraft", "physician", "biologist",
        "accountant", "paralegal", "legal assistant", "corporate assistant", "notariat",
        "immobilienbewirtschafter", "property manager", "art advisor", "bäcker", "konditor", "farben"
    ]):
        return JobEvaluation(
            is_relevant=False, match_score=1, role_category="Other",
            degree_fit="Retail / Non-professional", language_req="N/A",
            track_alignment="Disqualified: Non-finance Field",
            fit_strengths="None",
            career_gaps="Requires non-finance engineering, medical, clerical, or non-target vocational domain.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: None | ⚠️ Gaps: Non-financial or clerical title.",
            scorer="heuristic",
        )

    # 3. Master thesis & Bachelor thesis exclusions
    if any(k in t_lower for k in ["master thesis", "masterarbeit", "master’s thesis", "bachelor thesis", "bachelorarbeit"]):
        return JobEvaluation(
            is_relevant=False, match_score=2, role_category="Other",
            degree_fit="Retail / Non-professional", language_req="N/A",
            track_alignment="Disqualified: Student Thesis",
            fit_strengths="Already holds Cambridge MPhil.",
            career_gaps="Student thesis project (candidate seeks professional employment).",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: Cambridge MPhil | ⚠️ Gaps: Student thesis project.",
            scorer="heuristic",
        )

    # 4. Academic PhD / Doctoral studentship exclusions
    if any(k in t_lower for k in ["phd position", "doctoral position", "phd student", "doktorand", "doctoral student", "phd in "]):
        return JobEvaluation(
            is_relevant=False, match_score=2, role_category="Other",
            degree_fit="Retail / Non-professional", language_req="N/A",
            track_alignment="Disqualified: Academic PhD Studentship",
            fit_strengths="Econometrics / quantitative overlap.",
            career_gaps="Candidate has 7+ years investment industry experience and seeks professional roles.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: Quantitative background | ⚠️ Gaps: Academic PhD studentship.",
            scorer="heuristic",
        )

    # 5. Core finance / investment domain requirement
    FINANCE_DOMAIN_REGEX = re.compile(
        r"(portfoli|asset manage|wealth manage|fund|invest|equity|fixed income|credit|quant|systematic|"
        r"derivat|hedg|private equity|private debt|venture capital|m&a|corporate finance|treasur|risk|"
        r"trad|capital market|anlag|verm\u00f6gen|wertpapier|vorsorge|pension|kader|analyst|associate|"
        r"director|banking|fintech|cio\b|multi-asset|fund select|manager select|family office)",
        re.I,
    )
    if not FINANCE_DOMAIN_REGEX.search(t_clean) and not FINANCE_DOMAIN_REGEX.search(d_clean[:1200]):
        return JobEvaluation(
            is_relevant=False, match_score=1, role_category="Other",
            degree_fit="Retail / Non-professional", language_req="N/A",
            track_alignment="Disqualified: Non-financial field",
            fit_strengths="None",
            career_gaps="No finance, asset management, investment, or quantitative domain found.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: None | ⚠️ Gaps: Non-financial domain.",
            scorer="heuristic",
        )

    # 6. Track and category heuristic mapping
    score = 5
    category = "Asset Management"
    track = "General Finance & Investment Management"

    if any(k in text for k in ["quant", "systematic", "algo", "factor model", "convex optimization", "cvxpy", "alpha", "desk quant"]):
        category = "Risk & Quantitative"
        track = "Track 1: Quantitative Portfolio Management & Systematic Strategies"
        score += 2
    elif any(k in text for k in ["equity analyst", "equity research", "single stock", "stock picking", "aktienanalyst", "quantamental", "fundamental equity"]):
        category = "Investment Research"
        track = "Track 2: Direct Equity Selection (Fundamental & Quantamental)"
        score += 2
    elif any(k in text for k in ["fund select", "manager select", "fund-of-fund", "due diligence", "fondsanalyst", "multi-manager", "external manager"]):
        category = "Asset Management"
        track = "Track 3: Head of Manager Selection / Multi-Manager & Fund Solutions"
        score += 2
    elif any(k in text for k in ["multi-asset", "mandate", "asset allocation", "vermögensverwaltung", "balanced mandate", "tactical asset allocation"]):
        category = "Asset Management"
        track = "Track 4: Head of Mandates, Multi-Asset PM & CIO Asset Allocation"
        score += 2
    elif any(k in text for k in ["investment specialist", "investment advisor", "portfolio counselor", "desk cio", "anlagestrateg", "bespoke portfolio"]):
        category = "Wealth Management"
        track = "Track 5: UHNW Investment Specialist / Bespoke Portfolio Counselor"
        score += 2
    elif any(k in text for k in ["client advisor", "relationship manager", "kundenberater", "private banker", "cee desk", "wealth planning"]):
        category = "Wealth Management"
        track = "Track 6: UHNW Client Advisor / Relationship Manager"
        score += 1
    elif any(k in text for k in ["family office", "sfo", "mfo", "family wealth"]):
        category = "Wealth Management"
        track = "Track 7: Single & Multi-Family Office CIO or Investment Director"
        score += 2
    elif any(k in text for k in ["pensionskasse", "vorsorge", "institutional allocator", "bvg", "sammeleinrichtung"]):
        category = "Asset Management"
        track = "Track 8: Swiss Pension Funds & Public Institutional Allocators"
        score += 1
    elif any(k in text for k in ["alm", "asset liability", "reinsurance", "insurance asset"]):
        category = "Asset Management"
        track = "Track 9: Insurance & Reinsurance Institutional Investments / ALM"
        score += 1
    elif any(k in text for k in ["private markets", "private equity", "private debt", "infrastructure", "secondary", "partners group"]):
        category = "Corporate Finance / PE"
        track = "Track 10: Private Markets Quantitative Portfolio Solutions"
        score += 1
    elif any(k in text for k in ["wealthtech", "assettech", "fintech", "quant dev", "sygnum", "swissquote", "six group"]):
        category = "Fintech & Markets"
        track = "Track 11: WealthTech, AssetTech & AI/Quant Platform Leadership"
        score += 1
    elif any(k in text for k in ["investment consult", "ocio", "outsourced cio", "fiduciary management"]):
        category = "Asset Management"
        track = "Track 12: Institutional Investment Consulting & Outsourced CIO"
        score += 1

    # 7. Seniority & credentials boost / penalty
    is_senior = any(k in t_lower for k in [
        "director", "head of", "lead", "senior portfolio manager", "senior analyst", "vp", "vice president", "principal", "investment specialist"
    ])
    is_mid = any(k in t_lower for k in ["portfolio manager", "analyst", "strategist", "researcher", "quant", "associate"])
    is_intern = any(k in t_lower for k in ["intern", "internship", "praktikant", "praktikum", "working student", "werkstudent"])
    is_c_suite = any(k in t_lower for k in ["managing director", "partner", "chief executive", "country head"])

    if is_senior:
        score += 1
        degree_fit = "Senior Director / PM Lead"
    elif is_intern:
        score -= 2
        degree_fit = "Entry / Junior Analyst"
    elif is_c_suite:
        degree_fit = "Overqualified (MD/Partner Req)"
    elif is_mid:
        degree_fit = "Charterholder / CFA Level II+"
    else:
        degree_fit = "MSc / CFA Suitable"

    # 8. Language check
    de_words = len(re.findall(r"\b(und|oder|wir|für|mit|aufgaben|profil|anforderungen|kenntnisse)\b", text))
    lang_req = "EN + DE B1/B2 OK" if de_words > 4 else "English (C1/C2)"
    if any(k in text for k in ["verhandlungssicher", "muttersprache", "c1", "c2", "fluent german required"]):
        lang_req = "Fluent DE Required (C1/C2)"
        if any(k in t_lower for k in ["client advisor", "relationship manager", "kundenberater"]):
            score -= 1

    # Heuristic score is capped between 1 and 7
    score = max(1, min(7, score))
    is_rel = (score >= 6)

    fit_str = f"Matches {category} background: Cambridge MPhil, CFA Charter, Director / PM track record, and quantitative toolkit."
    gap_str = "Heuristic fallback evaluation - requires Gemini LLM audit."
    summary = f"🎯 Track: {track} | ✅ Fit: {fit_str} | ⚠️ Gaps: {gap_str}"

    return JobEvaluation(
        is_relevant=is_rel,
        match_score=score,
        role_category=category,
        degree_fit=degree_fit,
        language_req=lang_req,
        track_alignment=track,
        fit_strengths=fit_str,
        career_gaps=gap_str,
        one_line_summary=summary,
        scorer="heuristic",
    )


# ---------------------------------------------------------------------------
# Gemini Flash evaluator (with automatic fallback cascade)
# ---------------------------------------------------------------------------

def evaluate_job(client, title: str, company: str, location: str, desc: str, source: str) -> JobEvaluation:
    """Uses Gemini Flash (with automatic cascade and CV/Career matching) for critical job evaluation."""
    # Fast guardrail: check foreign locations or hard negative keywords
    t_clean = title.strip()
    loc_clean = (location or "").strip()
    d_clean = (desc or "").strip()
    if cfg.FOREIGN_LOCATIONS_REGEX.search(t_clean) or cfg.FOREIGN_LOCATIONS_REGEX.search(loc_clean):
        return JobEvaluation(
            is_relevant=False, match_score=1, role_category="Other",
            degree_fit="Foreign Location", language_req="N/A",
            track_alignment="Disqualified: Outside Switzerland",
            fit_strengths="None",
            career_gaps="Position is located outside Switzerland.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: None | ⚠️ Gaps: Position located outside Switzerland.",
            scorer="gemini",
        )
    if cfg.NEGATIVE_ROLE_KEYWORDS.search(t_clean):
        return JobEvaluation(
            is_relevant=False, match_score=2, role_category="Other",
            degree_fit="Disqualified Title", language_req="N/A",
            track_alignment="Disqualified: Non-target track",
            fit_strengths="None",
            career_gaps="Retail branch, clerical, bookkeeping, IT helpdesk, facility, or non-target title.",
            one_line_summary="🎯 Track: Disqualified | ✅ Fit: None | ⚠️ Gaps: Disqualified clerical, retail, or non-finance title.",
            scorer="gemini",
        )

    if not client:
        return evaluate_job_heuristic(title, company, desc, source, location=location)

    desc_clean = d_clean if len(d_clean) >= 30 else f"Position: {title} at {company} in {location}."

    cv_text = cfg.get_candidate_cv()
    career_directions_text = cfg.get_candidate_career_directions()

    prompt = f"""
You are an uncompromising, senior Swiss financial hiring auditor, asset management partner, and private banking recruitment director in Zurich.
Your task is to critically evaluate a job opening against the candidate's exact verified financial CV and envisioned career tracks (Tracks 1-12).
Be skeptical and rigorous: do NOT flatter or produce polite, generic confirmations. Call out misalignments, domain differences, seniority mismatches, and language requirements plainly.

=== CANDIDATE FULL VERIFIED CV ===
{cv_text}

=== ENVISIONED CAREER DIRECTIONS & TARGET FINANCIAL TRACKS ===
{career_directions_text}

=== JOB VACANCY TO EVALUATE ===
Job Title: {title}
Company: {company}
Location: {location}
Source: {source}
Description:
{desc_clean[:5500]}

=== CRITICAL EVALUATION RULES ===

1. RIGOROUS CALIBRATION & SCORING:
   - 9-10 (Exceptional / Dream Fit): Near-perfect alignment with Target Tracks (e.g. Track 1 Quant PM/Systematic, Track 2 Direct Equity Selection, Track 3 Head of Manager Selection, Track 4 Multi-Asset PM / CIO Asset Allocation, Track 5 UHNW Desk CIO, Track 7 Family Office CIO/Director). Candidate's credentials (UBS GWM Director, Cambridge MPhil, CFA Charterholder, GRE 170 Quant, Python/cvxpy factor models, $4B+ direct fund track record, $160B team AuM) directly cover 80%+ of core duties. Gaps are minor/negligible. Level fits Director / Senior PM (7-10y experience).
   - 7-8 (Strong Target Match): Strong financial/investment fit in Swiss asset management, private banking, hedge funds, or institutional allocators. Solid match on portfolio management, investment research, or quant analysis. Minor bridgeable gaps (e.g. specific niche asset class, learning firm-specific proprietary platform).
   - 6 (Viable Baseline): Relevant financial role (e.g. broader risk management, corporate finance, junior private banking advisory, investment consulting). Viable and within commute, but slight deviation from primary tracks or seniority.
   - 4-5 (Poor Fit / Misaligned): Misaligned financial domain (e.g. pure back-office bookkeeping, retail branch counter teller, standard treasury operations, underwriting without portfolio context, routine regulatory reporting).
   - 1-3 (Disqualified / Dealbreakers): Exclude immediately (is_relevant=false). Managing Partner / C-suite requiring 20+ years, non-finance jobs, junior apprenticeships / retail tellers, foreign location (outside Switzerland), or requiring native/C2 German for domestic retail client advisory.

2. SPECIFIC INSTRUCTIONS FOR OUTPUT FIELDS:
   - role_category: One of 'Asset Management', 'Wealth Management', 'Investment Research', 'Risk & Quantitative', 'Corporate Finance / PE', 'Fintech & Markets', 'Operations / Compliance', 'Other'.
   - degree_fit: One of 'Charterholder / CFA Level II+', 'Senior Director / PM Lead', 'MSc / CFA Suitable', 'Entry / Junior Analyst', 'Overqualified (MD/Partner Req)', 'Retail / Non-professional'.
   - language_req: One of 'English (C1/C2)', 'EN + DE B1/B2 OK', 'Fluent DE Required (C1/C2)'.
   - track_alignment: Identify precisely which of Envisioned Tracks 1-12 this advances (e.g. "Track 1: Quantitative Portfolio Management & Systematic Strategies"). If tangential or misaligned, state clearly.
   - fit_strengths: Name the EXACT verified credentials, track records, and technical skills from his CV that match the vacancy duties (e.g. "Direct overlap with Cambridge MPhil econometrics, CFA charter, UBS GWM Portfolio Manager managing $4B+ across single-name/multi-asset/fund-of-funds, and Python cvxpy factor models"). Be specific; avoid generic praise.
   - career_gaps: Honestly identify what the candidate lacks. Probe for:
     * Domain / Strategy Mismatch: Discretionary multi-asset / fund selection vs. pure high-frequency execution or physical commodity trading.
     * Level / Credentials: Demands Managing Partner with 20+ years vs. candidate's Director / 7+ years PM profile, or under-leveled intern roles.
     * Language: Demands Swiss German / German C1/C2 for local retail clients vs. candidate's professional English C2 and conversational German B1/B2.
     (If gaps are minimal, state: "Minimal gaps: core duties align directly with candidate's asset management and quantitative toolkit.")
   - one_line_summary: Combine the three dimensions in this exact format:
     "🎯 Track: <track_alignment> | ✅ Fit: <fit_strengths> | ⚠️ Gaps: <career_gaps>"
"""

    models_to_try = [
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.8-flash",
        "gemini-3.5-flash",
    ]
    for attempt in range(2):
        for model_name in models_to_try:
            try:
                resp = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config={
                        "response_mime_type": "application/json",
                        "response_schema": JobEvaluation,
                        "temperature": 0.1,
                    },
                )
                ev = JobEvaluation.model_validate_json(resp.text)
                ev.scorer = "gemini"
                # Enforce structured summary format
                if "🎯 Track:" not in ev.one_line_summary or "✅ Fit:" not in ev.one_line_summary or "⚠️ Gaps:" not in ev.one_line_summary:
                    ev.one_line_summary = f"🎯 Track: {ev.track_alignment} | ✅ Fit: {ev.fit_strengths} | ⚠️ Gaps: {ev.career_gaps}"
                return ev
            except Exception as e:
                # If exhausted or not found, try next model immediately
                continue

    print(f"  [WARN] LLM evaluation failed for '{title[:30]}', using updated heuristic fallback.")
    return evaluate_job_heuristic(title, company, desc, source, location=location)


# ---------------------------------------------------------------------------
# Batch re-scorer for existing DB rows
# ---------------------------------------------------------------------------

def rescore_database_jobs(conn: sqlite3.Connection, client, limit: Optional[int] = None) -> None:
    """Re-scores existing jobs stored in finance_jobs.db using the enhanced critical evaluation system."""
    if not client:
        print("[!] GEMINI_API_KEY is not set or google-genai is not available. Cannot rescore.")
        return

    cur = conn.cursor()
    query = """
        SELECT job_hash, title, company, location, url, source, summary 
        FROM jobs 
        ORDER BY is_relevant DESC, match_score DESC
    """
    if limit:
        query += f" LIMIT {int(limit)}"
    cur.execute(query)
    rows = cur.fetchall()
    total = len(rows)

    print(f"[*] Re-scoring {total} jobs in finance_jobs.db using critical Gemini Flash evaluation...")
    print("    (Fast-path for disqualified titles; paced at 1.5s intervals for active positions)")

    updated = 0
    for i, (jhash, title, company, location, url, source, old_summary) in enumerate(rows, 1):
        t_clean = (title or "").strip()
        loc_clean = (location or "").strip()
        d_clean = (old_summary or "").strip()
        is_fast_disqualified = (
            bool(cfg.FOREIGN_LOCATIONS_REGEX.search(t_clean))
            or bool(cfg.FOREIGN_LOCATIONS_REGEX.search(loc_clean))
            or bool(cfg.NEGATIVE_ROLE_KEYWORDS.search(t_clean))
        )

        desc_to_eval = d_clean
        if not is_fast_disqualified and url and len(d_clean) < 150:
            body = fetch_job_description_body(url, timeout=2.5)
            if body and len(body) > len(desc_to_eval):
                desc_to_eval = body

        ev = evaluate_job(client, title, company, location, desc_to_eval, source)
        cur.execute(
            """UPDATE jobs
               SET match_score = ?, is_relevant = ?, role_category = ?, degree_fit = ?,
                   language_req = ?, summary = ?, scorer = ?
               WHERE job_hash = ?""",
            (
                ev.match_score,
                1 if ev.is_relevant else 0,
                ev.role_category,
                ev.degree_fit,
                ev.language_req,
                ev.one_line_summary,
                ev.scorer,
                jhash,
            ),
        )
        conn.commit()
        updated += 1
        print(f"  [{i}/{total}] {title[:35]} @ {company[:18]} -> {ev.match_score}/10 ({ev.role_category}) [{ev.scorer}]", flush=True)
        if not is_fast_disqualified and i < total:
            time.sleep(1.5)

    print(f"[+] Successfully rescored {updated} jobs in finance_jobs.db!")


def rescore_heuristic_fallbacks(conn: sqlite3.Connection, client, limit: int = None, stop_on_quota_error: bool = True) -> int:
    """
    Finds any jobs evaluated with heuristic fallback (scorer = 'heuristic' or legacy summary)
    and re-evaluates them using Gemini to ensure 100% critical audit coverage.
    Ordered by match_score DESC so highest-priority candidates are upgraded first.
    Includes a circuit-breaker to stop early if daily quota is exhausted.
    """
    if not client:
        print("[!] No Gemini client available to rescore heuristic fallbacks.")
        return 0

    cur = conn.cursor()
    query = """
        SELECT job_hash, title, company, location, url, source, summary, match_score
        FROM jobs
        WHERE scorer = 'heuristic'
           OR summary LIKE '%Heuristic fallback evaluation%'
        ORDER BY match_score DESC
    """
    if limit:
        query += f" LIMIT {int(limit)}"

    cur.execute(query)
    rows = cur.fetchall()
    if not rows:
        print("[*] No heuristic fallback jobs to rescore. All jobs are Gemini-verified!")
        return 0

    print(f"[*] Found {len(rows)} heuristic fallback jobs. Re-evaluating via Gemini Flash...")
    rescored = 0
    consecutive_failures = 0
    for jhash, title, company, location, url, source, old_summary, old_score in rows:
        desc_to_eval = ""
        if url:
            body = fetch_job_description_body(url, timeout=3.0)
            if body and len(body) > 80:
                desc_to_eval = body
        if not desc_to_eval:
            desc_to_eval = f"{company} financial position ({location}): {title}. Source: {source}."

        ev = evaluate_job(client, title, company, location, desc_to_eval, source)
        if ev.scorer == "gemini":
            consecutive_failures = 0
            cur.execute("""
                UPDATE jobs
                SET match_score = ?, is_relevant = ?, role_category = ?, degree_fit = ?,
                    language_req = ?, summary = ?, scorer = 'gemini'
                WHERE job_hash = ?
            """, (
                ev.match_score,
                1 if ev.is_relevant else 0,
                ev.role_category,
                ev.degree_fit,
                ev.language_req,
                ev.one_line_summary,
                jhash,
            ))
            conn.commit()
            rescored += 1
            print(f"  [Rescored Gemini] {title[:35]} @ {company[:18]} -> was {old_score}/10, now {ev.match_score}/10 ({ev.role_category})")
        else:
            consecutive_failures += 1
            # If Gemini still failed, update row with clean conservative heuristic
            cur.execute("""
                UPDATE jobs
                SET match_score = ?, is_relevant = ?, role_category = ?, degree_fit = ?,
                    language_req = ?, summary = ?, scorer = 'heuristic'
                WHERE job_hash = ?
            """, (
                ev.match_score,
                1 if ev.is_relevant else 0,
                ev.role_category,
                ev.degree_fit,
                ev.language_req,
                ev.one_line_summary,
                jhash,
            ))
            conn.commit()
            print(f"  [Kept Heuristic] {title[:35]} @ {company[:18]} -> calibrated heuristic {old_score}/10 -> {ev.match_score}/10")
            if stop_on_quota_error and consecutive_failures >= 2:
                print("  [!] Gemini quota unavailable or exhausted. Pausing heuristic rescoring pass until next run.")
                break
        time.sleep(1.0)

    print(f"[+] Re-scored {rescored}/{len(rows)} heuristic fallback jobs via Gemini!")
    return rescored
