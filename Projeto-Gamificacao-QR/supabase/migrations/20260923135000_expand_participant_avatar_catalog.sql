-- Expande o catálogo de avatares internos de 12 para 20 opções.
-- Mantém as chaves existentes e não altera qualquer regra de gamificação.

alter table public.participants
  drop constraint if exists participants_avatar_key_check;

alter table public.participants
  add constraint participants_avatar_key_check
  check (avatar_key ~ '^avatar-(0[1-9]|1[0-9]|20)$');
