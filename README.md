# MarketLens Cloud Scanner

Cloud runtime for MarketLens V4.3.1.

## Security
- Keep the repository private.
- Never commit `SUPABASE_SERVICE_ROLE_KEY`.
- GitHub Actions requires repository secrets `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY`.
- The browser dashboard continues to use only the Supabase publishable key.

## Scanner
- Preserves the V4 iBay parser behavior.
- Preserves the V4.3.1 classification rules.
- Rotates through persisted iBay source sections.
- Writes listings, categories, snapshots and run status to Supabase.
- Never deactivates listings because a partial scan omitted them.

## Manual local test

```bash
python -m pytest tests/scanner -q
```

## GitHub Actions
The `MarketLens Cloud Scan` workflow supports manual dispatch and a scheduled run every four hours. Change the cadence later only after observing runtime and source behavior.
