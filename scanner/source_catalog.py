"""Verified public source catalog for MarketLens multi-source discovery."""

SOURCES = {
    "ibay": {
        "name": "iBay Maldives",
        "base_url": "https://ibay.com.mv/",
        "kind": "marketplace",
        "priority": 10,
        "enabled": True,
        "discovery_mode": "native",
        "signals": ("wanted", "jobs", "services", "for sale"),
    },
    "gazette": {
        "name": "Maldives Gazette",
        "base_url": "https://gazette.gov.mv/iulaan",
        "path_regex": r"^/iulaan/\\d+$",
        "kind": "official",
        "priority": 20,
        "enabled": True,
        "discovery_mode": "links",
        "signals": (
            "job opportunity",
            "vacancy",
            "quotation",
            "tender",
            "bid",
            "procurement",
            "consultancy",
            "service",
            "supply",
            "purchase",
        ),
    },
    "jobcenter": {
        "name": "Job Center Maldives",
        "base_url": "https://beta.jobcenter.mv/en/jobs",
        "path_regex": r"^/en/jobs/[^/?#]+$",
        "kind": "jobs",
        "priority": 30,
        "enabled": True,
        "discovery_mode": "links",
        "signals": (
            "job",
            "vacancy",
            "hiring",
            "employer",
            "training",
            "apprenticeship",
        ),
    },
}


def enabled_sources():
    return [
        {"key": key, **config}
        for key, config in SOURCES.items()
        if config.get("enabled", False)
    ]


def get_source(key):
    try:
        return {"key": key, **SOURCES[key]}
    except KeyError as exc:
        raise KeyError(f"Unknown MarketLens source: {key}") from exc
