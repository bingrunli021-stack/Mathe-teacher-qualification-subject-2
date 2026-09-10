-- Protected, administrator-managed exam settings.
create table if not exists public.tq_site_settings(
  key text primary key,
  value jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.tq_site_settings enable row level security;
revoke all on public.tq_site_settings from anon,authenticated;
grant select on public.tq_site_settings to authenticated;
drop policy if exists tq_private_read on public.tq_site_settings;
create policy tq_private_read on public.tq_site_settings for select to authenticated
using(exists(select 1 from public.tq_members where user_id=(select auth.uid())));
insert into public.tq_site_settings(key,value) values
('exam_date','{"date":null,"official":false,"status":"等待官方公布"}'::jsonb)
on conflict(key) do nothing;

-- Score objective questions on the server and attach the review interval.
create or replace function public.tq_score_answer() returns trigger
language plpgsql security invoker set search_path='' as $$
declare q jsonb; is_correct boolean; prior_streak int; review_days int;
begin
  if new.kind <> 'answer' then return new; end if;
  select question into q
  from public.tq_content c
  cross join lateral jsonb_array_elements(c.questions) question
  where c.id=new.unit_id and question->>'id'=new.payload->>'question_id'
  limit 1;
  if q is null then raise exception 'Invalid question'; end if;
  if coalesce(new.payload->>'response','')='' then raise exception 'Answer required'; end if;
  if q->>'type' in ('choice','judgement') then
    is_correct := new.payload->>'response' = q->>'answer';
  else
    if jsonb_typeof(new.payload->'correct') is distinct from 'boolean' then raise exception 'Self assessment required'; end if;
    is_correct := (new.payload->>'correct')::boolean;
  end if;
  if is_correct then
    select count(*) into prior_streak from public.tq_events e
    where e.user_id=new.user_id and e.unit_id=new.unit_id and e.kind='answer'
      and (e.payload->>'correct')::boolean
      and e.seq > coalesce((select max(w.seq) from public.tq_events w where w.user_id=new.user_id and w.unit_id=new.unit_id and w.kind='answer' and not (w.payload->>'correct')::boolean),0);
    review_days := case when prior_streak=0 then 1 when prior_streak=1 then 3 when prior_streak=2 then 7 when prior_streak=3 then 14 else 30 end;
  else review_days := 1;
  end if;
  new.payload := jsonb_build_object(
    'question_id',new.payload->>'question_id',
    'response',left(new.payload->>'response',10000),
    'correct',is_correct,
    'type',q->>'type',
    'review_days',review_days
  );
  return new;
end $$;
revoke all on function public.tq_score_answer() from public,anon,authenticated;
drop trigger if exists tq_answer_score on public.tq_events;
create trigger tq_answer_score before insert on public.tq_events
for each row execute function public.tq_score_answer();
