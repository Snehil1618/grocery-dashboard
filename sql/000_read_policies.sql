-- 000_read_policies.sql
-- ALREADY APPLIED on 24 Oct 2026. Kept as a record of the database setup.
-- Lets the app (anon key, server-side only) read the two data tables.
-- Without these, RLS makes Supabase return empty lists and the dashboard looks empty.

create policy "anon read receipts"   on receipts   for select to anon using (true);
create policy "anon read line_items" on line_items for select to anon using (true);
