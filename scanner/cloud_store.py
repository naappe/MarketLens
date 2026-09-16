"""Supabase persistence adapter for the MarketLens cloud scanner."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone

TRACKED_FIELDS = (
    "title",
    "price_mvr",
    "category_id",
    "status",
    "url",
    "listing_type",
    "subcategory",
    "classification_confidence",
    "classification_reason",
    "source_category",
    "market_intent",
    "job_direction",
    "job_role",
    "job_salary_min_mvr",
    "job_salary_max_mvr",
    "public_phone",
    "public_email",
)


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def slugify(value):
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "other"


def sort_sections(sections):
    return sorted(
        sections,
        key=lambda row: (
            row.get("last_scan_at") is not None,
            row.get("last_scan_at") or "",
            int(row.get("priority") or 100),
            row.get("name") or "",
        ),
    )


def tracked_changes(old, new):
    merged = dict(new)
    if merged.get("price_mvr") is None and old.get("price_mvr") is not None:
        merged["price_mvr"] = old.get("price_mvr")
    changed = [field for field in TRACKED_FIELDS if old.get(field) != merged.get(field)]
    return changed, merged


def raw_hash(payload):
    stable = {field: payload.get(field) for field in TRACKED_FIELDS}
    data = json.dumps(stable, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


class CloudStore:
    def __init__(self, client):
        self.client = client
        self._category_ids = {}

    def source_id(self, name="iBay Maldives"):
        response = self.client.table("marketlens_sources").select("id").eq("name", name).limit(1).execute()
        rows = response.data or []
        if not rows:
            raise RuntimeError(f"MarketLens source not found: {name}")
        return rows[0]["id"]

    def start_scan_run(self, source_id, trigger_type):
        payload = {"source_id": source_id, "status": "running", "trigger_type": trigger_type}
        response = self.client.table("marketlens_scan_runs").insert(payload).execute()
        return response.data[0]["id"]

    def finish_scan_run(self, run_id, *, status, counters, runtime_seconds, notes=None):
        payload = {
            "finished_at": now_iso(),
            "status": status,
            "runtime_seconds": round(runtime_seconds, 3),
            "notes": notes,
            **counters,
        }
        self.client.table("marketlens_scan_runs").update(payload).eq("id", run_id).execute()

    def upsert_sections(self, source_id, sections):
        rows = [
            {
                "source_id": source_id,
                "name": section["name"],
                "url": section["url"],
                "section_type": section["type"],
                "enabled": True,
                "priority": 10 if section["type"] == "wanted" else 100,
            }
            for section in sections
        ]
        if rows:
            self.client.table("marketlens_source_sections").upsert(
                rows, on_conflict="source_id,url"
            ).execute()

    def next_sections(self, source_id, limit):
        response = (
            self.client.table("marketlens_source_sections")
            .select("id,name,url,section_type,priority,last_scan_at,failure_count")
            .eq("source_id", source_id)
            .eq("enabled", True)
            .execute()
        )
        return sort_sections(response.data or [])[:limit]

    def mark_section_success(self, section_id, found):
        self.client.table("marketlens_source_sections").update(
            {
                "last_scan_at": now_iso(),
                "last_status": "OK",
                "last_items_found": int(found),
                "failure_count": 0,
            }
        ).eq("id", section_id).execute()

    def mark_section_error(self, section, error):
        self.client.table("marketlens_source_sections").update(
            {
                "last_scan_at": now_iso(),
                "last_status": "ERROR",
                "failure_count": int(section.get("failure_count") or 0) + 1,
                "last_error": str(error)[:1000],
            }
        ).eq("id", section["id"]).execute()

    def ensure_category(self, name):
        if name in self._category_ids:
            return self._category_ids[name]
        slug = slugify(name)
        response = self.client.table("marketlens_categories").select("id").eq("slug", slug).limit(1).execute()
        rows = response.data or []
        if rows:
            category_id = rows[0]["id"]
        else:
            inserted = self.client.table("marketlens_categories").insert(
                {"name": name, "slug": slug, "active": True}
            ).execute()
            category_id = inserted.data[0]["id"]
        self._category_ids[name] = category_id
        return category_id

    def upsert_listing(self, source_id, item, classification, scan_run_id, source_category, job_fields=None):
        top, subcategory, intent, confidence, reason = classification
        category_id = self.ensure_category(top)
        lookup = (
            self.client.table("marketlens_listings")
            .select(
                "id,title,price_mvr,category_id,status,url,listing_type,subcategory,"
                "classification_confidence,classification_reason,source_category,market_intent,"
                "job_direction,job_role,job_salary_min_mvr,job_salary_max_mvr,public_phone,public_email"
            )
            .eq("source_id", source_id)
            .eq("external_id", str(item["listing_id"]))
            .limit(1)
            .execute()
        )
        existing_rows = lookup.data or []
        current = {
            "title": item["title"],
            "price_mvr": item.get("price"),
            "category_id": category_id,
            "status": "active",
            "url": item["url"],
            "listing_type": item["type"],
            "subcategory": subcategory,
            "classification_confidence": int(confidence),
            "classification_reason": reason,
            "source_category": source_category,
            "market_intent": intent,
            "job_direction": None,
            "job_role": None,
            "job_salary_min_mvr": None,
            "job_salary_max_mvr": None,
            "public_phone": None,
            "public_email": None,
            **(job_fields or {}),
        }
        ts = now_iso()

        if not existing_rows:
            payload = {
                "source_id": source_id,
                "external_id": str(item["listing_id"]),
                "first_seen_at": ts,
                "last_seen_at": ts,
                **current,
            }
            self.client.table("marketlens_listings").insert(payload).execute()
            return "inserted"

        old = existing_rows[0]
        changes, merged = tracked_changes(old, current)
        self.client.table("marketlens_listings").update(
            {**merged, "last_seen_at": ts}
        ).eq("id", old["id"]).execute()

        if changes:
            self.client.table("marketlens_listing_snapshots").insert(
                {
                    "listing_id": old["id"],
                    "captured_at": ts,
                    "price_mvr": merged.get("price_mvr"),
                    "category_id": merged.get("category_id"),
                    "status": merged.get("status"),
                    "raw_hash": raw_hash(merged),
                    "scan_run_id": scan_run_id,
                }
            ).execute()
            return "updated"
        return "unchanged"
