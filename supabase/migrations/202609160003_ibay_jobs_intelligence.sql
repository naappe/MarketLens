alter table public.marketlens_listings
  add column if not exists job_direction text
    check (job_direction is null or job_direction in ('Hiring','Job Seeker','Other')),
  add column if not exists job_role text,
  add column if not exists job_salary_min_mvr integer
    check (job_salary_min_mvr is null or job_salary_min_mvr >= 0),
  add column if not exists job_salary_max_mvr integer
    check (job_salary_max_mvr is null or job_salary_max_mvr >= 0),
  add column if not exists public_phone text,
  add column if not exists public_email text;

create index if not exists marketlens_listings_jobs_direction_idx
  on public.marketlens_listings(source_id, job_direction, job_role)
  where source_category = 'Jobs' and status = 'active';
