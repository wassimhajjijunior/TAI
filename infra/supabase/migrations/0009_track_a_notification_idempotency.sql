alter table if exists notifications
  add column if not exists event_id uuid;

create unique index if not exists notifications_event_template_recipient_uidx
  on notifications(event_id, template_name, recipient_email)
  where event_id is not null;
