"""GitHub Actions entry point for the MarketLens cloud iBay scanner."""

import os
import time

from supabase import create_client

from scanner.classifier_v431 import classify
from scanner.cloud_store import CloudStore
from scanner.ibay_v4 import discover_categories, extract_page
from scanner.job_intelligence import job_fields_for_section


def trigger_type():
    return "schedule" if os.getenv("GITHUB_EVENT_NAME") == "schedule" else "manual"


def scan_limit():
    raw = os.getenv("SCAN_LIMIT", "10")
    value = int(raw)
    if not 1 <= value <= 50:
        raise RuntimeError("SCAN_LIMIT must be between 1 and 50")
    return value


def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url:
        raise RuntimeError("SUPABASE_URL is required")
    if not key:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required")

    started = time.monotonic()
    store = CloudStore(create_client(url, key))
    source_id = store.source_id("iBay Maldives")
    run_id = store.start_scan_run(source_id, trigger_type())
    counters = {
        "discovered_count": 0,
        "inserted_count": 0,
        "updated_count": 0,
        "unchanged_count": 0,
        "deactivated_count": 0,
        "error_count": 0,
    }
    errors = []
    successful_pages = 0

    try:
        sections = discover_categories()
        if not sections:
            raise RuntimeError("iBay category discovery returned no sections")
        store.upsert_sections(source_id, sections)
        selected = store.next_sections(source_id, scan_limit())
        if not selected:
            raise RuntimeError("No enabled iBay source sections are available")

        for section in selected:
            try:
                items = extract_page(section["url"], section["section_type"])
                counters["discovered_count"] += len(items)
                for item in items:
                    classification = classify(
                        item["title"], section["name"], item["type"]
                    )
                    result = store.upsert_listing(
                        source_id,
                        item,
                        classification,
                        run_id,
                        source_category=section["name"],
                        job_fields=job_fields_for_section(section["name"], item),
                    )
                    counters[f"{result}_count"] += 1
                store.mark_section_success(section["id"], len(items))
                successful_pages += 1
            except Exception as exc:  # section failure is partial, not destructive
                counters["error_count"] += 1
                errors.append(f"{section['name']}: {exc}")
                store.mark_section_error(section, exc)

        if successful_pages == 0:
            status = "failed"
        elif counters["error_count"]:
            status = "partial"
        else:
            status = "succeeded"

        store.finish_scan_run(
            run_id,
            status=status,
            counters=counters,
            runtime_seconds=time.monotonic() - started,
            notes="\n".join(errors)[:4000] or None,
        )
        print(
            "MARKETLENS CLOUD SCAN",
            status.upper(),
            f"pages={successful_pages}",
            f"found={counters['discovered_count']}",
            f"inserted={counters['inserted_count']}",
            f"updated={counters['updated_count']}",
            f"unchanged={counters['unchanged_count']}",
            f"errors={counters['error_count']}",
        )
        return 1 if status == "failed" else 0
    except Exception as exc:
        counters["error_count"] += 1
        errors.append(str(exc))
        store.finish_scan_run(
            run_id,
            status="failed",
            counters=counters,
            runtime_seconds=time.monotonic() - started,
            notes="\n".join(errors)[:4000],
        )
        raise


if __name__ == "__main__":
    raise SystemExit(main())
