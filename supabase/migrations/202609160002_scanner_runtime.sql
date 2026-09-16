create table if not exists public.marketlens_source_sections (
  id uuid primary key default gen_random_uuid(),
  source_id uuid not null references public.marketlens_sources(id) on delete cascade,
  name text not null,
  url text not null,
  section_type text not null check (section_type in ('category','wanted')),
  enabled boolean not null default true,
  priority integer not null default 100,
  last_scan_at timestamptz,
  last_status text check (last_status is null or last_status in ('OK','ERROR')),
  last_items_found integer not null default 0 check (last_items_found >= 0),
  failure_count integer not null default 0 check (failure_count >= 0),
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique(source_id, url)
);

create index if not exists marketlens_source_sections_rotation_idx
  on public.marketlens_source_sections(source_id, enabled, last_scan_at, priority);

alter table public.marketlens_listings
  add column if not exists subcategory text,
  add column if not exists classification_confidence integer
    check (classification_confidence is null or classification_confidence between 0 and 100),
  add column if not exists classification_reason text,
  add column if not exists market_intent text
    check (market_intent is null or market_intent in ('Wanted','For Sale'));

alter table public.marketlens_source_sections enable row level security;

drop policy if exists "marketlens authorized read source sections" on public.marketlens_source_sections;
create policy "marketlens authorized read source sections"
on public.marketlens_source_sections for select to authenticated
using (marketlens_private.has_access());

drop policy if exists "marketlens admins manage source sections" on public.marketlens_source_sections;
create policy "marketlens admins manage source sections"
on public.marketlens_source_sections for all to authenticated
using (marketlens_private.is_admin())
with check (marketlens_private.is_admin());

drop trigger if exists marketlens_source_sections_set_updated_at on public.marketlens_source_sections;
create trigger marketlens_source_sections_set_updated_at
before update on public.marketlens_source_sections
for each row execute function public.marketlens_set_updated_at();
