"""Pure iBay V4 discovery/extraction logic ported from MarketLens V4."""

import re
from urllib.parse import urljoin, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup

HOME = "https://ibay.com.mv"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 Chrome/152 Safari/537.36"
}
LISTING_RE = re.compile(r"-o(\d+)\.html$", re.I)
CATEGORY_RE = re.compile(r"-b\d+(?:_\d+)?\.html$", re.I)
PRICE_PATTERNS = [
    re.compile(r"\bMVR\s*([\d,]+(?:\.\d{1,2})?)", re.I),
    re.compile(r"\bMRF\s*([\d,]+(?:\.\d{1,2})?)", re.I),
    re.compile(r"\bRF\.?\s*([\d,]+(?:\.\d{1,2})?)", re.I),
    re.compile(r"\b([\d,]+(?:\.\d{1,2})?)\s*/[-=]", re.I),
]


def clean(value):
    return " ".join((value or "").split())


def canonical(url):
    parsed = urlparse(url)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))


def listing_id(url):
    match = LISTING_RE.search(urlparse(url).path)
    return match.group(1) if match else None


def price_from_text(text):
    text = clean(text)
    for pattern in PRICE_PATTERNS:
        match = pattern.search(text)
        if match:
            try:
                value = float(match.group(1).replace(",", ""))
                if 0 <= value <= 50_000_000:
                    return value
            except ValueError:
                pass
    return None


def fetch(url):
    response = requests.get(url, headers=HEADERS, timeout=25)
    response.raise_for_status()
    return response.text


def discover_categories_html(html):
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for anchor in soup.find_all("a", href=True):
        url = canonical(urljoin(HOME, anchor["href"]))
        path = urlparse(url).path
        if not CATEGORY_RE.search(path):
            continue
        name = clean(anchor.get_text(" ", strip=True))
        if not name:
            name = path.rsplit("/", 1)[-1].split("-b")[0].replace("-", " ").title()
        section_type = "wanted" if ("wanted" in path.lower() or "wanted" in name.lower()) else "category"
        found[url] = {"name": name[:200], "url": url, "type": section_type}
    return list(found.values())


def discover_categories():
    return discover_categories_html(fetch(HOME))


def extract_page_html(html, url, source_type):
    soup = BeautifulSoup(html, "html.parser")
    found = {}
    for anchor in soup.find_all("a", href=True):
        absolute = canonical(urljoin(url, anchor["href"]))
        lid = listing_id(absolute)
        if not lid:
            continue
        title = clean(anchor.get_text(" ", strip=True))
        if not title:
            continue
        context = title
        parent = anchor.parent
        for _ in range(3):
            if parent is None:
                break
            value = clean(parent.get_text(" ", strip=True))
            if value and len(value) > len(context):
                context = value
            parent = parent.parent
        item = {
            "listing_id": lid,
            "title": title[:400],
            "url": absolute,
            "type": "wanted" if source_type == "wanted" else "for_sale",
            "price": price_from_text(context),
        }
        old = found.get(lid)
        if old is None or len(item["title"]) > len(old["title"]):
            found[lid] = item
    return list(found.values())


def extract_page(url, source_type):
    return extract_page_html(fetch(url), url, source_type)
