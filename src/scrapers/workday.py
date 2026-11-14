"""Workday CXS direct JSON API scraper for major Swiss financial institutions and asset managers."""

from typing import List, Dict

import requests

from src.config import cfg


def fetch_workday_apis() -> List[Dict]:
    """Queries hidden Workday JSON endpoints directly for configured companies."""
    companies = ", ".join(t["company"] for t in cfg.WORKDAY_TARGETS)
    print(f"[4/6] Querying Workday Direct JSON APIs ({companies})...")
    results: List[Dict] = []
    wd_headers = {
        **cfg.HEADERS,
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    seen_urls = set()
    for target in cfg.WORKDAY_TARGETS:
        for term in target["search_terms"]:
            payload = {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": term}
            try:
                r = requests.post(target["api_url"], headers=wd_headers, json=payload, timeout=8)
                if r.ok:
                    data = r.json()
                    for post in data.get("jobPostings", []):
                        title = post.get("title", "")
                        loc = post.get("locationsText", target["default_location"])
                        ext_path = post.get("externalPath", "")
                        if not title or not ext_path:
                            continue
                        # Filter to target commutable locations
                        loc_lower = loc.lower()
                        if not any(k in loc_lower for k in cfg.TARGET_LOCATIONS_LOWER):
                            continue

                        # Filter by positive and negative role keywords
                        if not cfg.POSITIVE_ROLE_KEYWORDS.search(title) or cfg.NEGATIVE_ROLE_KEYWORDS.search(title):
                            continue

                        job_url = f"{target['site_url'].rstrip('/')}{ext_path}"
                        if job_url in seen_urls:
                            continue
                        seen_urls.add(job_url)

                        results.append({
                            "title": title,
                            "company": target["company"],
                            "location": loc,
                            "url": job_url,
                            "description": (
                                f"{target['company']} role ({loc}): {title}"
                                f" - {post.get('bulletFields', '')}"
                            ),
                            "source": "Workday Direct API",
                        })
            except Exception:
                continue
    print(f"  -> Retrieved {len(results)} Swiss listings from Workday APIs.")
    return results
