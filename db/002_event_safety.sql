-- Extend the existing append-only design without deleting content or user data.
create index if not exists tq_catalog_parent_idx on public.tq_catalog(parent_id);
create index if not exists tq_timer_events_idx on public.tq_events(user_id,seq desc) where kind='time';
do $$ declare c record; begin
 for c in select conname from pg_constraint where conrelid='public.tq_events'::regclass and contype='c' and pg_get_constraintdef(oid) like '%seconds%' loop
  execute format('alter table public.tq_events drop constraint %I',c.conname);
 end loop;
end $$;
alter table public.tq_events add constraint tq_time_bound check(kind<>'time' or (payload->>'seconds')::int between 0 and 45);
create or replace function public.tq_validate_event() returns trigger language plpgsql security invoker set search_path='' as $$
declare prev public.tq_events; secs int:=0; today date:=(now() at time zone 'Asia/Shanghai')::date; first_day date; d date; missed int:=0; goal int; ids jsonb;
begin
 if new.user_id is distinct from auth.uid() then raise exception 'User mismatch'; end if;
 perform pg_advisory_xact_lock(hashtextextended(new.user_id::text,47));
 new.created_at:=clock_timestamp();
 if new.kind not in ('settings','plan') and (new.unit_id is null or not exists(select 1 from public.tq_catalog where id=new.unit_id and kind='point')) then raise exception 'Knowledge point required'; end if;
 if new.kind='status' and coalesce(new.payload->>'value','') not in ('未学习','学习中','模糊','已掌握') then raise exception 'Invalid status'; end if;
 if new.kind='answer' and (jsonb_typeof(new.payload->'correct') is distinct from 'boolean' or not exists(select 1 from public.tq_content c,jsonb_array_elements(c.questions) q where c.id=new.unit_id and q->>'id'=new.payload->>'question_id')) then raise exception 'Invalid question'; end if;
 if new.kind='time' then
  if coalesce(new.payload->>'action','') not in ('start','tick','stop') or coalesce(new.payload->>'device','')='' then raise exception 'Invalid timer'; end if;
  select * into prev from public.tq_events where user_id=new.user_id and kind='time' order by seq desc limit 1;
  if new.payload->>'action'='start' and prev.payload->>'action' in ('start','tick') and new.created_at-prev.created_at<interval '45 seconds' then raise exception '另一页面正在计时，请先暂停或等待45秒'; end if;
  if new.payload->>'action' in ('tick','stop') then
   if prev.id is null or prev.payload->>'action' not in ('start','tick') or prev.payload->>'device' is distinct from new.payload->>'device' or prev.unit_id is distinct from new.unit_id then raise exception '计时已结束或在另一页面进行，请重新开始'; end if;
   if new.created_at-prev.created_at<=interval '45 seconds' then secs:=greatest(0,floor(extract(epoch from new.created_at-prev.created_at))); end if;
  end if;
  new.payload:=jsonb_build_object('action',new.payload->>'action','device',new.payload->>'device','seconds',secs);
 end if;
 if new.kind='plan' then
  if new.payload->>'day' is distinct from today::text then raise exception '只能生成今日计划'; end if;
  select min((created_at at time zone 'Asia/Shanghai')::date) into first_day from public.tq_events where user_id=new.user_id and kind='plan';
  for d in select generate_series(today-3,today-1,interval '1 day')::date loop
   if first_day<=d then
    select coalesce((select (payload->>'goal')::int from public.tq_events where user_id=new.user_id and kind='plan' and payload->>'day'=d::text),1500) into goal;
    if (select coalesce(sum((payload->>'seconds')::int),0) from public.tq_events where user_id=new.user_id and kind='time' and (created_at at time zone 'Asia/Shanghai')::date=d)<goal then missed:=missed+1; end if;
   end if;
  end loop;
  select coalesce(jsonb_agg(id),'[]') into ids from (
   select c.id from public.tq_catalog c
   left join lateral (select created_at,payload from public.tq_events where user_id=new.user_id and unit_id=c.id and kind='answer' order by seq desc limit 1) a on true
   left join lateral (select payload from public.tq_events where user_id=new.user_id and unit_id=c.id and kind='status' order by seq desc limit 1) s on true
   where c.kind='point' and c.ready
   order by case when a.payload->>'correct'='false' then 0 when s.payload->>'value'='模糊' then 1 when a.created_at<now()-interval '3 days' then 2 when a.created_at is null and coalesce(s.payload->>'value','未学习')<>'已掌握' then 3 else 4 end, a.created_at nulls first,c.sort_order
   limit case when missed=3 then 1 else 3 end
  ) chosen;
  new.payload:=jsonb_build_object('day',today::text,'goal',case when missed=3 then 600 else 1500 end,'point_ids',ids,'replanned',missed=3);
 end if;
 return new;
end $$;
create or replace function public.tq_clock() returns timestamptz language sql stable security invoker set search_path='' as $$select now()$$;
revoke all on function public.tq_clock() from public,anon;
grant execute on function public.tq_clock() to authenticated;
