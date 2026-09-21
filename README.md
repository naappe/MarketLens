# MarketLens Cloud Scanner

Cloud runtime for MarketLens V4.4 multi-source opportunity discovery.

## Security
- Keep the repository private.
- Never commit `SUPABASE_SERVICE_ROLE_KEY`.
- GitHub Actions requires repository secrets `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
- The browser dashboard continues to use only the Supabase publishable key.

## Sources
MarketLens now has a source registry so new Maldives sources can be added without changing the iBay parser.

1. **iBay Maldives** — primary marketplace source; native V4 parser remains unchanged.
2. **Maldives Gazette** — official jobs, tenders, quotations, procurement, supply and consultancy opportunities.
3. **Job Center Maldives** — formal jobs, hiring, training and apprenticeship opportunities.

The source catalog lives in `scanner/source_catalog.py`.

## Scanner
- Preserves the V4 iBay parser behavior.
- Preserves the V4.3.1 classification rules.
- Rotates through persisted iBay source sections.
- Writes iBay listings, categories, snapshots and run status to Supabase.
- Never deactivates listings because a partial scan omitted them.
- Adds generic same-domain opportunity-link discovery for sources that do not use the iBay parser.
- Scores links by demand signals such as wanted, need, quotation, tender, procurement, vacancy, hiring, consultancy, supply and purchase.

## Opportunity link search

Run all enabled link-discovery sources:

```bash
python -m scanner.link_search --source all --limit 25
```

Or inspect one source:

```bash
python -m scanner.link_search --source gazette --limit 25
python -m scanner.link_search --source jobcenter --limit 25
```

iBay is intentionally excluded from generic link crawling because it already has the stronger native parser in `scanner/ibay_v4.py`.

## Manual local test

```bash
python -m pytest tests/scanner -q
```

## GitHub Actions
The `MarketLens Cloud Scan` workflow supports manual dispatch and a scheduled run every four hours. The current scheduled database ingestion remains iBay-first. Multi-source link discovery is being added as a separate, non-destructive intelligence layer before additional source-specific database ingestion is enabled.
