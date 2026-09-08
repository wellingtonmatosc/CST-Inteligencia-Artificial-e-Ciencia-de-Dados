-- Proteção mínima contra tentativa automatizada de PIN de 4 dígitos.
alter table public.participants
    add column if not exists pin_failed_attempts smallint not null default 0,
    add column if not exists pin_locked_until timestamptz;

alter table public.participants
    drop constraint if exists participants_pin_failed_attempts_check;
alter table public.participants
    add constraint participants_pin_failed_attempts_check
    check (pin_failed_attempts between 0 and 20);
