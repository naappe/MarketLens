"""iBay Jobs classification, public contact extraction, and lightweight matching."""

from __future__ import annotations

import re
from bs4 import BeautifulSoup

SEEKER_PHRASES = (
    "job seeking",
    "seeking a job",
    "seeking job",
    "looking for a job",
    "looking for job",
    "need a job",
    "need job",
    "available for job",
    "available for work",
    "looking for work",
    "currently looking for a job",
)

HIRING_PHRASES = (
    "we are hiring",
    "we're hiring",
    "hiring",
    "job vacancy",
    "vacancy",
    "looking for a",
    "looking for an",
    "needed",
    "need a worker",
    "need worker",
    "need cashier",
    "need staff",
    "join our team",
    "candidates are requested",
)

ROLE_ALIASES = {
    "cashier": ("cashier",),
    "waitress": ("waitress", "waiter", "server"),
    "sales assistant": ("sales assistant", "sales staff", "salesperson"),
    "receptionist": ("receptionist", "front office"),
    "housekeeper": ("housekeeper", "house keeper", "housekeeping", "house maid", "housemaid"),
    "babysitter": ("babysitter", "baby sitter", "babysitting"),
    "driver": ("driver", "delivery guy", "delivery man", "rider"),
    "accountant": ("accountant", "accounting officer", "accounts officer"),
    "admin": ("admin officer", "admin assistant", "administrative"),
    "teacher": ("teacher", "tutor"),
    "security": ("security", "security guard"),
    "technician": ("technician",),
}

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?960[\s-]*)?[279]\d{2}[\s-]*\d{4}(?!\d)")
SALARY_RANGE_RE = re.compile(
    r"(?:rf|mvr)\s*([\d,]+)\s*(?:to|[-–])\s*(?:rf|mvr)?\s*([\d,]+)", re.I
)


def _clean(value):
    return " ".join((value or "").split())


def classify_job_direction(title, text=""):
    haystack = f"{title or ''} {text or ''}".lower()
    if any(phrase in haystack for phrase in SEEKER_PHRASES):
        return "Job Seeker"
    if any(phrase in haystack for phrase in HIRING_PHRASES):
        return "Hiring"
    return "Other"


def extract_job_role(title, text=""):
    haystack = f"{title or ''} {text or ''}".lower()
    for canonical, aliases in ROLE_ALIASES.items():
        if any(alias in haystack for alias in aliases):
            return canonical
    words = re.findall(r"[a-z]+", (title or "").lower())
    ignored = {"job", "vacancy", "needed", "hiring", "female", "male", "only", "full", "time", "part"}
    kept = [word for word in words if word not in ignored]
    return " ".join(kept[:4]) or None


def extract_public_contact(text):
    text = _clean(text)
    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)
    email = email_match.group(0) if email_match else None
    phone = None
    if phone_match:
        digits = re.sub(r"\D", "", phone_match.group(0))
        if digits.startswith("960"):
            phone = "+" + digits
        else:
            phone = digits
    return phone, email


def parse_salary_range(text):
    match = SALARY_RANGE_RE.search(_clean(text))
    if not match:
        return None, None
    return int(match.group(1).replace(",", "")), int(match.group(2).replace(",", ""))


def _label_value(soup, label):
    label_lower = label.lower()
    nodes = soup.find_all(string=lambda s: s and _clean(str(s)).lower() == label_lower)
    for node in nodes:
        parent = node.parent
        sibling = parent.find_next_sibling() if parent else None
        if sibling:
            value = _clean(sibling.get_text(" ", strip=True))
            if value:
                return value
        if parent:
            nxt = parent.find_next()
            if nxt and nxt is not parent:
                value = _clean(nxt.get_text(" ", strip=True) if hasattr(nxt, "get_text") else str(nxt))
                if value and value.lower() != label_lower:
                    return value
    return None


def extract_job_detail_html(html):
    soup = BeautifulSoup(html or "", "html.parser")
    text = _clean(soup.get_text(" ", strip=True))
    salary_text = _label_value(soup, "Salary Range") or text
    salary_min, salary_max = parse_salary_range(salary_text)
    phone, email = extract_public_contact(text)
    title_node = soup.find(["h1", "h2", "h3"])
    title = _clean(title_node.get_text(" ", strip=True)) if title_node else ""
    return {
        "job_direction": classify_job_direction(title, text),
        "job_role": extract_job_role(title, text),
        "employer": _label_value(soup, "Employer"),
        "location": _label_value(soup, "Location"),
        "position_type": _label_value(soup, "Position Type"),
        "job_salary_min_mvr": salary_min,
        "job_salary_max_mvr": salary_max,
        "public_phone": phone,
        "public_email": email,
    }


def analyze_job_listing(title, text=""):
    salary_min, salary_max = parse_salary_range(text)
    phone, email = extract_public_contact(text)
    return {
        "job_direction": classify_job_direction(title, text),
        "job_role": extract_job_role(title, text),
        "job_salary_min_mvr": salary_min,
        "job_salary_max_mvr": salary_max,
        "public_phone": phone,
        "public_email": email,
    }


def job_match_score(left, right):
    directions = {left.get("job_direction"), right.get("job_direction")}
    if directions != {"Hiring", "Job Seeker"}:
        return 0
    left_role = _clean(left.get("job_role") or "").lower()
    right_role = _clean(right.get("job_role") or "").lower()
    if left_role and right_role and left_role == right_role:
        return 95
    left_tokens = set(re.findall(r"[a-z]+", f"{left_role} {left.get('title') or ''}".lower()))
    right_tokens = set(re.findall(r"[a-z]+", f"{right_role} {right.get('title') or ''}".lower()))
    useful = (left_tokens & right_tokens) - {"job", "full", "part", "time", "male", "female"}
    return min(85, 55 + 10 * len(useful)) if useful else 0


def job_fields_for_section(section_name, item):
    if (section_name or "").strip().lower() != "jobs":
        return None
    return analyze_job_listing(item.get("title", ""), item.get("summary", ""))
