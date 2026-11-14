#!/usr/bin/env python3
"""
Zurich Finance, Asset Management & Wealth Management Job Radar — CLI Entry Point

Tailored for: Director & Quantitative Portfolio Manager (Cambridge MPhil, CFA Charterholder, GRE 170 Quant, Python/R, $4B+ AuM)
Commute origin: Glattbrugg / Zurich Area (<= 60 min transit or car to Zurich Paradeplatz, Zug/Baar, Pfäffikon SZ)

Configuration lives in config/targets.yaml.
Business logic lives in the src/ package.
"""

import argparse
import os
import subprocess
import webbrowser
from datetime import datetime

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from src.config import cfg
from src.database import init_db, make_job_hash
from src.commute import get_commute_info
from src.evaluator import evaluate_job, rescore_database_jobs, rescore_heuristic_fallbacks
from src.dashboard import generate_html_dashboard
from src.scrapers.jobspy_aggregator import fetch_jobspy_aggregators
from src.scrapers.workday import fetch_workday_apis
from src.scrapers.career_pages import fetch_curated_career_pages
from src.scrapers.jobs_ch import fetch_jobs_ch
from src.scrapers.startup_apis import fetch_startup_api_jobs
from src.scrapers.description_fetcher import fetch_job_description_body
from src.notify import send_daily_email_digest


def publish_to_github(commit_msg: str = None) -> bool:
    """Stages updated dashboard/index files and commits & pushes to GitHub Pages."""
    if not commit_msg:
        commit_msg = f"Update dashboard ({datetime.now().strftime('%Y-%m-%d %H:%M')})"
    try:
        files_to_add = [
            str(cfg.REPORT_PATH),
            str(cfg.INDEX_PATH),
            str(cfg.DOCS_INDEX_PATH),
            str(cfg.PROJECT_ROOT / "finance_jobs.db"),
            str(cfg.PROJECT_ROOT / ".nojekyll"),
            str(cfg.DOCS_DIR / ".nojekyll"),
            str(cfg.PROJECT_ROOT / ".gitignore"),
            str(cfg.PROJECT_ROOT / "src"),
            str(cfg.PROJECT_ROOT / "config"),
            str(cfg.PROJECT_ROOT / "zurich_finance_radar.py"),
            str(cfg.PROJECT_ROOT / "zurich_chem_radar.py"),
            str(cfg.PROJECT_ROOT / "ROADMAP.md"),
            str(cfg.PROJECT_ROOT / "README.md"),
            str(cfg.PROJECT_ROOT / "Makefile"),
            str(cfg.PROJECT_ROOT / "run_daily.sh"),
        ]
        existing = [f for f in files_to_add if os.path.exists(f)]
        subprocess.run(["git", "add"] + existing, check=True, cwd=str(cfg.PROJECT_ROOT))

        diff_res = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=str(cfg.PROJECT_ROOT))
        if diff_res.returncode == 0:
            print("[publish] No changes to commit (everything up-to-date).")
            return True

        subprocess.run(["git", "commit", "-m", commit_msg], check=True, cwd=str(cfg.PROJECT_ROOT))
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=str(cfg.PROJECT_ROOT))
        print("[publish] Successfully pushed updated dashboard to GitHub Pages!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[publish ERROR] Git command failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Zurich Finance, Asset Management & Wealth Management Job Radar")
    parser.add_argument("--hours", type=int, default=72, help="Lookback hours for JobSpy (default: 72)")
    parser.add_argument("--no-browser", action="store_true", help="Do not auto-open HTML dashboard")
    parser.add_argument("--skip-jobspy", action="store_true", help="Skip aggregator scraping (Indeed/LinkedIn/Google)")
    parser.add_argument("--skip-jobs-ch", action="store_true", help="Skip jobs.ch REST API scan")
    parser.add_argument("--skip-workday", action="store_true", help="Skip Workday CXS endpoints scan")
    parser.add_argument("--skip-startup-apis", action="store_true", help="Skip direct fintech JSON APIs scan")
    parser.add_argument("--skip-career-pages", action="store_true", help="Skip curated career pages scan")
    parser.add_argument(
        "--jobspy-sites",
        nargs="+",
        default=["indeed", "linkedin"],
        help="Aggregator sites to scan (default: indeed, linkedin; options: indeed, linkedin, google).",
    )
    parser.add_argument("--rescore", action="store_true", help="Re-score all existing jobs using Gemini 2.5 Flash")
    parser.add_argument("--rescore-limit", type=int, default=None, help="Limit number of jobs to rescore")
    parser.add_argument("--rescore-heuristic", action="store_true", help="Re-score only jobs that were evaluated with the heuristic fallback")
    parser.add_argument("--dashboard-only", action="store_true", help="Re-generate dashboard and index.html from DB without scraping")
    parser.add_argument("--publish", action="store_true", help="Auto-commit and push updated dashboard/index to GitHub Pages")
    parser.add_argument("--notify", action="store_true", help="Send daily email digest to configured recipients")
    parser.add_argument("--test-email", action="store_true", help="Send a test email with recent top jobs and exit")

    # Backward compatibility flags (ignored)
    parser.add_argument("--skip-spinoff-crawl", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-myscience", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-lifesciencework", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-scs", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--skip-givaudan", action="store_true", help=argparse.SUPPRESS)

    args = parser.parse_args()

    conn = init_db()
    client = (
        genai.Client(
            api_key=cfg.GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=15000),
        )
        if (HAS_GENAI and cfg.GEMINI_API_KEY)
        else None
    )
    if client:
        print("[INFO] Gemini Flash semantic scoring ENABLED (gemini-2.5-flash / 3.5-flash).")
    else:
        print("[INFO] Running with built-in Financial/Quantitative heuristic scorer (set GEMINI_API_KEY to enable LLM scoring).")

    # --test-email mode: test email connectivity with top high-match jobs
    if args.test_email:
        print("[*] Preparing test email digest with top high-match jobs...")
        cur = conn.cursor()
        cur.execute(
            """
            SELECT count(*) FROM jobs
            WHERE is_relevant = 1 AND match_score >= 6 AND commute_mins <= ?
            """,
            (cfg.MAX_COMMUTE_MINS + 5,),
        )
        total_matching = cur.fetchone()[0]

        cur.execute(
            """
            SELECT title, company, location, url, commute_mins, commute_mode,
                   match_score, role_category, degree_fit, summary
            FROM jobs
            WHERE match_score >= 8 AND is_relevant = 1 AND commute_mins <= ?
            ORDER BY match_score DESC, commute_mins ASC
            LIMIT ?
            """,
            (cfg.MAX_COMMUTE_MINS + 5, cfg.MAX_EMAIL_JOBS),
        )
        sample_jobs = [
            {
                "title": r[0],
                "company": r[1],
                "location": r[2],
                "url": r[3],
                "commute_mins": r[4],
                "commute_mode": r[5],
                "match_score": r[6],
                "role_category": r[7],
                "degree_fit": r[8],
                "summary": r[9],
            }
            for r in cur.fetchall()
        ]
        send_daily_email_digest(
            jobs=sample_jobs,
            conn=conn,
            force=True,
            total_count=len(sample_jobs),
            overall_count=total_matching,
            is_test=True,
        )
        return

    # --dashboard-only mode: re-render HTML files from DB without scraping
    if args.dashboard_only:
        generate_html_dashboard(conn)
        if args.publish:
            publish_to_github()
        if not args.no_browser:
            webbrowser.open(f"file://{cfg.REPORT_PATH}")
        return

    # --rescore mode: re-evaluate existing DB rows via Gemini, then regenerate dashboard
    if args.rescore:
        if not client:
            print("[ERROR] Cannot run --rescore: GEMINI_API_KEY is not set or google-genai is not installed.")
            return
        rescore_database_jobs(conn, client, limit=args.rescore_limit)
        generate_html_dashboard(conn)
        if args.publish:
            publish_to_github()
        print(f"[+] Re-generated {cfg.REPORT_PATH}")
        if not args.no_browser:
            webbrowser.open(f"file://{cfg.REPORT_PATH}")
        return

    # --rescore-heuristic mode: re-evaluate only jobs that used the heuristic fallback
    if args.rescore_heuristic:
        if not client:
            print("[ERROR] Cannot run --rescore-heuristic: GEMINI_API_KEY is not set or google-genai is not installed.")
            return
        rescore_heuristic_fallbacks(conn, client)
        generate_html_dashboard(conn)
        if args.publish:
            publish_to_github()
        print(f"[+] Re-generated {cfg.REPORT_PATH}")
        if not args.no_browser:
            webbrowser.open(f"file://{cfg.REPORT_PATH}")
        return

    # Financial Scraping Pipeline
    raw_jobs = []

    # 1. Aggregators (JobSpy - Indeed & LinkedIn)
    if not args.skip_jobspy:
        raw_jobs.extend(fetch_jobspy_aggregators(hours_old=args.hours, sites=args.jobspy_sites))
    else:
        print("[1/5] Skipping JobSpy aggregators (--skip-jobspy passed).")

    # 2. Workday CXS APIs (Partners Group, Julius Bär, Vontobel, Swiss Re, Zurich Insurance, Pictet, LGT)
    if not args.skip_workday:
        raw_jobs.extend(fetch_workday_apis())
    else:
        print("[2/5] Skipping Workday CXS APIs (--skip-workday passed).")

    # 3. Direct Fintech & Digital Asset APIs (Greenhouse, Lever, etc.)
    if not args.skip_startup_apis:
        raw_jobs.extend(fetch_startup_api_jobs())
    else:
        print("[3/5] Skipping direct fintech JSON APIs (--skip-startup-apis passed).")

    # 4. Curated Financial Career Pages
    if not args.skip_career_pages:
        raw_jobs.extend(fetch_curated_career_pages())
    else:
        print("[4/5] Skipping curated career pages (--skip-career-pages passed).")

    # 5. Swiss Portal REST API (jobs.ch)
    if not args.skip_jobs_ch:
        raw_jobs.extend(fetch_jobs_ch())
    else:
        print("[5/5] Skipping jobs.ch API (--skip-jobs-ch passed).")

    print(f"[*] Filtering {len(raw_jobs)} listings: checking database for duplicates and SBB commute limit...")
    cur = conn.cursor()

    already_seen_count = 0
    commute_exceeded_count = 0
    to_evaluate = []
    seen_in_batch = set()

    for item in raw_jobs:
        title = item.get("title", "").strip()
        company = item.get("company", "").strip()
        location = item.get("location", "Zurich").strip()
        url = item.get("url", "").strip()
        desc = item.get("description", "")
        source = item.get("source", "")

        if not title or not url:
            continue

        jhash = make_job_hash(company, title)
        if jhash in seen_in_batch:
            continue
        seen_in_batch.add(jhash)

        cur.execute("SELECT 1 FROM jobs WHERE job_hash = ?", (jhash,))
        if cur.fetchone():
            already_seen_count += 1
            continue

        commute_mins, commute_mode = get_commute_info(conn, location)
        is_basel_corridor = any(
            hub in location.lower()
            for hub in ["basel", "bâle", "reinach", "pratteln", "liestal"]
        )
        if commute_mins > (cfg.MAX_COMMUTE_MINS + 5) and not is_basel_corridor:
            commute_exceeded_count += 1
            continue

        to_evaluate.append({
            "jhash": jhash,
            "title": title,
            "company": company,
            "location": location,
            "url": url,
            "desc": desc,
            "source": source,
            "commute_mins": commute_mins,
            "commute_mode": commute_mode,
        })

    print(f"  -> Discarded {already_seen_count} already recorded.")
    print(f"  -> Discarded {commute_exceeded_count} beyond {cfg.MAX_COMMUTE_MINS}m commute limit.")
    print(f"[*] Evaluating {len(to_evaluate)} new listings via critical Gemini Flash scoring...")

    inserted_count = 0
    high_match_count = 0
    today_str = datetime.now().strftime("%Y-%m-%d")

    for i, job in enumerate(to_evaluate, 1):
        title = job["title"]
        company = job["company"]
        location = job["location"]
        url = job["url"]
        desc = job["desc"]
        source = job["source"]

        # Fast disqualify check before fetching external description
        t_clean = title.strip()
        loc_clean = location.strip()
        is_fast_disqualified = (
            bool(cfg.FOREIGN_LOCATIONS_REGEX.search(t_clean))
            or bool(cfg.FOREIGN_LOCATIONS_REGEX.search(loc_clean))
            or bool(cfg.NEGATIVE_ROLE_KEYWORDS.search(t_clean))
        )

        desc_to_eval = desc
        if not is_fast_disqualified and url and len(desc) < 150:
            body = fetch_job_description_body(url, timeout=3.0)
            if body and len(body) > len(desc_to_eval):
                desc_to_eval = body

        evaluation = evaluate_job(client, title, company, location, desc_to_eval, source)

        cur.execute(
            """INSERT INTO jobs
               (job_hash, title, company, location, url, source, commute_mins, commute_mode,
                match_score, is_relevant, role_category, degree_fit, language_req, summary, scorer, date_found)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                job["jhash"],
                title,
                company,
                location,
                url,
                source,
                job["commute_mins"],
                job["commute_mode"],
                evaluation.match_score,
                1 if evaluation.is_relevant else 0,
                evaluation.role_category,
                evaluation.degree_fit,
                evaluation.language_req,
                evaluation.one_line_summary,
                evaluation.scorer,
                today_str,
            ),
        )
        conn.commit()
        inserted_count += 1

        score_tag = f"{evaluation.match_score}/10"
        if evaluation.match_score >= 8:
            high_match_count += 1
            print(f"  [{i}/{len(to_evaluate)}] [HIGH MATCH {score_tag}] {title[:38]} @ {company[:18]} (~{job['commute_mins']}m) [{evaluation.scorer}]", flush=True)
        elif evaluation.match_score >= 6:
            print(f"  [{i}/{len(to_evaluate)}] [VIABLE {score_tag}] {title[:38]} @ {company[:18]} (~{job['commute_mins']}m) [{evaluation.scorer}]", flush=True)
        else:
            print(f"  [{i}/{len(to_evaluate)}] [LOW {score_tag}] {title[:38]} @ {company[:18]} [{evaluation.scorer}]", flush=True)

    print(f"\n[+] Pipeline run complete:")
    print(f"    - Evaluated & inserted: {inserted_count} new positions")
    print(f"    - High matches (>=8/10): {high_match_count} positions")

    generate_html_dashboard(conn)

    # Send daily notification digest
    if args.notify:
        send_daily_email_digest(conn=conn)

    # Auto-publish to GitHub Pages if requested
    if args.publish:
        publish_to_github()

    if not args.no_browser:
        webbrowser.open(f"file://{cfg.REPORT_PATH}")


if __name__ == "__main__":
    main()
