"""Build the static MarketLens GitHub Pages opportunity feed."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone, date
from pathlib import Path

from scanner.ibay_v4 import discover_categories, extract_page
from scanner.link_search import discover_all_links

OUT = Path("site/data/opportunities.json")

DATE_PATTERNS = (
    re.compile(r"\b(20\d{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])\b"),
    re.compile(r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2})\b"),
)
DEADLINE_WORDS = ("deadline", "closing", "close", "expires", "expiry", "last date", "due date", "submission")


def _score_ibay(item, section_name):
    score = 82 if item.get("type") == "wanted" else 55
    title = (item.get("title") or "").lower()
    for phrase, points in (
        ("need", 8),
        ("wanted", 10),
        ("looking for", 10),
        ("job", 6),
        ("service", 6),
        ("urgent", 5),
    ):
        if phrase in title:
            score += points
    return min(100, score)


def _date_candidates(text):
    text = text or ""
    out = []
    for pattern in DATE_PATTERNS:
        for match in pattern.finditer(text):
            parts = match.groups()
            try:
                if len(parts[0]) == 4:
                    dt = date(int(parts[0]), int(parts[1]), int(parts[2]))
                else:
                    dt = date(int(parts[2]), int(parts[1]), int(parts[0]))
                out.append((match.start(), dt))
            except ValueError:
                pass
    return out


def _timing_fields(title="", summary=""):
    text = " ".join(x for x in (title, summary) if x)
    lower = text.lower()
    candidates = _date_candidates(text)
    today = datetime.now(timezone.utc).date()

    detected_date = None
    expiry_date = None

    if candidates:
        detected_date = min(dt for _, dt in candidates)

        deadline_hits = []
        for pos, dt in candidates:
            context = lower[max(0, pos - 45): pos + 45]
            if any(word in context for word in DEADLINE_WORDS):
                deadline_hits.append(dt)

        future_dates = [dt for _, dt in candidates if dt >= today]
        if deadline_hits:
            expiry_date = min(deadline_hits)
        elif future_dates:
            expiry_date = min(future_dates)

    days_left = None
    status = "No deadline"
    if expiry_date:
        days_left = (expiry_date - today).days
        if days_left < 0:
            status = "Expired"
        elif days_left <= 3:
            status = "Expiring soon"
        else:
            status = "Active"

    return {
        "detected_date": detected_date.isoformat() if detected_date else None,
        "expiry_date": expiry_date.isoformat() if expiry_date else None,
        "days_left": days_left,
        "status": status,
    }


def collect_ibay(limit_sections=8, per_section=30):
    rows = []
    sections = discover_categories()
    sections.sort(key=lambda s: (s.get("type") != "wanted", s.get("name") or ""))
    for section in sections[:limit_sections]:
        try:
            for item in extract_page(section["url"], section["type"])[:per_section]:
                timing = _timing_fields(item.get("title"), item.get("summary"))
                rows.append(
                    {
                        "source_key": "ibay",
                        "source_name": "iBay Maldives",
                        "title": item.get("title") or "iBay listing",
                        "url": item.get("url"),
                        "score": _score_ibay(item, section.get("name")),
                        "kind": "Wanted" if item.get("type") == "wanted" else "Marketplace",
                        "price_mvr": item.get("price"),
                        "section": section.get("name"),
                        **timing,
                    }
                )
        except Exception as exc:
            rows.append(
                {
                    "source_key": "ibay",
                    "source_name": "iBay Maldives",
                    "title": f"Scan warning: {section.get('name')}",
                    "url": section.get("url"),
                    "score": 0,
                    "kind": "System",
                    "error": str(exc)[:200],
                    "detected_date": None,
                    "expiry_date": None,
                    "days_left": None,
                    "status": "Unavailable",
                }
            )
    return rows


def collect_links():
    rows, errors = discover_all_links()
    mapped = []
    for row in rows:
        title = row.get("title") or "Opportunity"
        lower = title.lower()
        if any(word in lower for word in ("tender", "quotation", "procurement", "bid", "supply")):
            kind = "Tender / Supply"
        elif any(word in lower for word in ("job", "vacancy", "hiring")):
            kind = "Jobs"
        elif any(word in lower for word in ("consult", "service")):
            kind = "Services"
        else:
            kind = "Opportunity"
        timing = _timing_fields(title, row.get("summary", ""))
        mapped.append(
            {
                **row,
                "kind": kind,
                "price_mvr": None,
                "section": None,
                **timing,
            }
        )
    return mapped, errors


def _sort_key(row):
    status_rank = {"Expiring soon": 0, "Active": 1, "No deadline": 2, "Expired": 3}
    expiry = row.get("expiry_date") or "9999-12-31"
    return (
        status_rank.get(row.get("status"), 4),
        expiry,
        -int(row.get("score") or 0),
        row.get("source_name") or "",
        row.get("title") or "",
    )


def main():
    opportunities = []
    errors = []
    generated_at = datetime.now(timezone.utc).isoformat()

    try:
        opportunities.extend(collect_ibay())
    except Exception as exc:
        errors.append({"source": "iBay Maldives", "error": str(exc)})

    try:
        rows, link_errors = collect_links()
        opportunities.extend(rows)
        errors.extend(link_errors)
    except Exception as exc:
        errors.append({"source": "Multi-source discovery", "error": str(exc)})

    seen = set()
    clean = []
    for row in sorted(opportunities, key=_sort_key):
        url = row.get("url")
        if not url or url in seen or row.get("score", 0) <= 0:
            continue
        seen.add(url)
        row["scanned_at"] = generated_at
        clean.append(row)

    payload = {
        "generated_at": generated_at,
        "count": len(clean),
        "sources": sorted({r.get("source_name") for r in clean if r.get("source_name")}),
        "errors": errors,
        "opportunities": clean[:300],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Built {len(payload['opportunities'])} opportunities")


if __name__ == "__main__":
    main()
