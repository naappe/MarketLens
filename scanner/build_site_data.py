"""Build the static MarketLens GitHub Pages opportunity feed."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from scanner.ibay_v4 import discover_categories, extract_page
from scanner.link_search import discover_all_links

OUT = Path("site/data/opportunities.json")


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


def collect_ibay(limit_sections=8, per_section=30):
    rows = []
    sections = discover_categories()
    sections.sort(key=lambda s: (s.get("type") != "wanted", s.get("name") or ""))
    for section in sections[:limit_sections]:
        try:
            for item in extract_page(section["url"], section["type"])[:per_section]:
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
        mapped.append({**row, "kind": kind, "price_mvr": None, "section": None})
    return mapped, errors


def main():
    opportunities = []
    errors = []

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
    for row in sorted(opportunities, key=lambda x: (-int(x.get("score") or 0), x.get("source_name") or "", x.get("title") or "")):
        url = row.get("url")
        if not url or url in seen or row.get("score", 0) <= 0:
            continue
        seen.add(url)
        clean.append(row)

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
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
