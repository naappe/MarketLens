"""Generic public-link discovery and opportunity scoring for MarketLens."""

from __future__ import annotations

import argparse
import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

from scanner.source_catalog import enabled_sources, get_source

DEFAULT_TIMEOUT = 20
USER_AGENT = "MarketLens/4.4 (+public opportunity discovery)"

HIGH_VALUE = {
    "wanted": 30,
    "need": 24,
    "looking for": 22,
    "quotation": 28,
    "tender": 28,
    "bid": 24,
    "procurement": 28,
    "job opportunity": 26,
    "vacancy": 24,
    "hiring": 22,
    "consultancy": 24,
    "service": 16,
    "supply": 18,
    "purchase": 18,
}

NOISE = {
    "privacy": -40,
    "terms": -40,
    "login": -25,
    "sign in": -25,
    "register": -15,
    "contact": -12,
    "about": -10,
    "facebook": -25,
    "instagram": -25,
}


def _clean(value):
    return " ".join((value or "").split())


def canonical_url(base_url, href):
    absolute = urljoin(base_url, href or "")
    parsed = urlparse(absolute)
    if parsed.scheme not in {"http", "https"}:
        return None
    return urlunparse((parsed.scheme, parsed.netloc.lower(), parsed.path, "", parsed.query, ""))


def same_host(url, base_url):
    return urlparse(url).netloc.lower() == urlparse(base_url).netloc.lower()


def opportunity_score(title, url, signals=()):
    haystack = f"{_clean(title)} {url}".lower()
    score = 0
    for phrase, weight in HIGH_VALUE.items():
        if phrase in haystack:
            score += weight
    for phrase in signals:
        if phrase.lower() in haystack:
            score += 12
    for phrase, weight in NOISE.items():
        if phrase in haystack:
            score += weight
    if re.search(r"/(?:iulaan|jobs?|vacanc|tender|procurement|wanted)", haystack):
        score += 20
    return max(0, min(100, score))


def extract_links(html, source):
    soup = BeautifulSoup(html or "", "html.parser")
    seen = set()
    rows = []
    for anchor in soup.find_all("a", href=True):
        title = _clean(anchor.get_text(" ", strip=True))
        url = canonical_url(source["base_url"], anchor.get("href"))
        if not url or not same_host(url, source["base_url"]) or url in seen:
            continue
        seen.add(url)
        score = opportunity_score(title, url, source.get("signals", ()))
        if score <= 0:
            continue
        rows.append(
            {
                "source_key": source["key"],
                "source_name": source["name"],
                "title": title or url,
                "url": url,
                "score": score,
            }
        )
    return sorted(rows, key=lambda row: (-row["score"], row["title"].lower()))


def discover_source_links(source_key, *, timeout=DEFAULT_TIMEOUT, session=None):
    source = get_source(source_key)
    if source["discovery_mode"] == "native":
        return []
    client = session or requests
    response = client.get(
        source["base_url"],
        timeout=timeout,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    return extract_links(response.text, source)


def discover_all_links(*, timeout=DEFAULT_TIMEOUT, session=None):
    results = []
    errors = []
    for source in enabled_sources():
        if source["discovery_mode"] != "links":
            continue
        try:
            results.extend(
                discover_source_links(source["key"], timeout=timeout, session=session)
            )
        except Exception as exc:
            errors.append({"source": source["name"], "error": str(exc)})
    results.sort(key=lambda row: (-row["score"], row["source_name"], row["title"].lower()))
    return results, errors


def main():
    parser = argparse.ArgumentParser(description="Discover high-value MarketLens opportunity links")
    parser.add_argument("--source", choices=[s["key"] for s in enabled_sources()] + ["all"], default="all")
    parser.add_argument("--limit", type=int, default=25)
    args = parser.parse_args()

    if args.source == "all":
        rows, errors = discover_all_links()
    else:
        rows = discover_source_links(args.source)
        errors = []

    for row in rows[: max(1, args.limit)]:
        print(f"{row['score']:>3}  {row['source_name']}: {row['title']}\n     {row['url']}")
    for error in errors:
        print(f"ERROR {error['source']}: {error['error']}")
    return 1 if errors and not rows else 0


if __name__ == "__main__":
    raise SystemExit(main())
