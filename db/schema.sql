begin;
create table public.tq_members(user_id uuid primary key references auth.users(id));
-- After migration, add the intended authenticated user's UUID to tq_members through an administrator connection.
create table public.tq_catalog(id text primary key, parent_id text references public.tq_catalog(id), kind text not null check(kind in ('chapter','section','point')), title text not null, sort_order int not null, page_start int not null, page_end int not null, ready boolean not null default false);
create table public.tq_content(id text primary key references public.tq_catalog(id), blocks jsonb not null default '[]', explanation text not null default '', exam text not null default '', pitfalls text not null default '', questions jsonb not null default '[]', verification text not null default '待核对', source_sha256 text not null);
create table public.tq_pages(pdf_page int primary key, printed_page int, image_data text not null, source_sha256 text not null);
create table public.tq_events(seq bigint generated always as identity primary key, id uuid unique not null, user_id uuid not null references auth.users(id), unit_id text references public.tq_catalog(id), kind text not null check(kind in ('status','note','highlight','bookmark','answer','time','settings','plan')), payload jsonb not null, created_at timestamptz not null default now(), check(pg_column_size(payload)<100000), check(kind <> 'time' or ((payload->>'seconds')::int between 1 and 30)));
create index on public.tq_events(user_id,seq);
create index on public.tq_events(unit_id);
alter table public.tq_members enable row level security;
create policy tq_member_self on public.tq_members for select to authenticated using(user_id=(select auth.uid()));
revoke all on public.tq_members from anon,authenticated;
grant select on public.tq_members to authenticated;
do $$ declare t text; begin foreach t in array array['tq_catalog','tq_content','tq_pages'] loop
 execute format('alter table public.%I enable row level security',t);
 execute format('revoke all on public.%I from anon,authenticated',t);
 execute format('grant select on public.%I to authenticated',t);
 execute format('create policy tq_private_read on public.%I for select to authenticated using(exists(select 1 from public.tq_members where user_id=(select auth.uid())))',t);
end loop; end $$;
alter table public.tq_events enable row level security;
revoke all on public.tq_events from anon,authenticated;
grant select on public.tq_events to authenticated;
grant insert(id,user_id,unit_id,kind,payload) on public.tq_events to authenticated;
grant usage on sequence public.tq_events_seq_seq to authenticated;
create policy tq_events_read on public.tq_events for select to authenticated using(user_id=(select auth.uid()) and exists(select 1 from public.tq_members where user_id=(select auth.uid())));
create policy tq_events_insert on public.tq_events for insert to authenticated with check(user_id=(select auth.uid()) and exists(select 1 from public.tq_members where user_id=(select auth.uid())));
-- Append-only history: no UPDATE/DELETE grants, no client-supplied server timestamps.
-- Plans are unique per day; retries and competing devices cannot duplicate them.
create unique index tq_one_plan_per_day on public.tq_events(user_id,((payload->>'day'))) where kind='plan';
create function public.tq_validate_event() returns trigger language plpgsql security invoker set search_path='' as $$
begin
 if new.kind='plan' and new.payload->>'day' <> to_char(now() at time zone 'Asia/Shanghai','YYYY-MM-DD') then raise exception '只能生成今日计划'; end if;
 return new;
end $$;
create trigger tq_event_validate before insert on public.tq_events for each row execute function public.tq_validate_event();
revoke all on function public.tq_validate_event() from public,anon,authenticated;
commit;
