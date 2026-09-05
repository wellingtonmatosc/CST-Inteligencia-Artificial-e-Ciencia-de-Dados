"""Configura bônus diário e bônus dinâmico em janelas de uma hora.

O script exige opções simultâneas em Cantina, Térreo e 1º andar. Assim, nenhuma
pessoa precisa usar escadas para ter acesso à mesma oportunidade de bônus.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.repositories.supabase_repo import SupabaseRepository
from app.services.bonus_schedule import REQUIRED_ZONES, hourly_windows, validate_zone_mapping


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configura os dois bônus de um dia do evento.")
    parser.add_argument("--config", required=True, type=Path, help="Arquivo JSON de configuração")
    return parser.parse_args()


def read_config(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Arquivo não encontrado: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"JSON inválido: {exc}") from exc


def get_zone_ids(repo: SupabaseRepository) -> dict[str, str]:
    rows = repo.raw_table("zones").select("id,slug").eq("active", True).execute().data or []
    result = {row["slug"]: row["id"] for row in rows}
    missing = [slug for slug in REQUIRED_ZONES if slug not in result]
    if missing:
        raise SystemExit("Zonas ausentes no banco: " + ", ".join(missing))
    return result


def resolve_qr(repo: SupabaseRepository, code: str, zone_id: str, expected_kind: str) -> dict:
    rows = repo.select("qr_points", code=code, active=True)
    if not rows:
        raise SystemExit(f"QR não encontrado/ativo: {code}")
    qr = rows[0]
    if qr["zone_id"] != zone_id:
        raise SystemExit(f"QR {code} não pertence à zona informada.")
    if qr["kind"] != expected_kind:
        raise SystemExit(f"QR {code} deveria ser do tipo {expected_kind}.")
    return qr


def upsert_campaign(repo: SupabaseRepository, event_date: str, bonus_type: str, name: str, points: int) -> dict:
    rows = repo.select("bonus_campaigns", event_date=event_date, bonus_type=bonus_type)
    if rows:
        campaign = rows[0]
        repo.update("bonus_campaigns", {"name": name, "points": points, "active": True}, id=campaign["id"])
        campaign.update({"name": name, "points": points, "active": True})
        return campaign
    return repo.insert("bonus_campaigns", {"event_date": event_date, "bonus_type": bonus_type, "name": name, "points": points, "active": True})


def clear_locations_if_safe(repo: SupabaseRepository, campaign_id: str) -> None:
    if repo.select("bonus_runs", campaign_id=campaign_id):
        raise SystemExit("Este bônus já possui participações e não pode ser reconfigurado automaticamente.")
    repo.delete("bonus_locations", campaign_id=campaign_id)


def main() -> None:
    args = parse_args()
    cfg = read_config(args.config)
    settings = get_settings()
    configure_logging(settings.log_level)
    logger = logging.getLogger(__name__)
    repo = SupabaseRepository(settings)

    event_date = date.fromisoformat(cfg["event_date"])
    start = time.fromisoformat(cfg["start_time"])
    end = time.fromisoformat(cfg["end_time"])
    daily_map = cfg["daily_qr_by_zone"]
    dynamic_map = cfg["dynamic_qrs_by_zone"]
    validate_zone_mapping(daily_map)
    validate_zone_mapping(dynamic_map)

    zone_ids = get_zone_ids(repo)
    daily = upsert_campaign(repo, event_date.isoformat(), "daily_bonus", cfg.get("daily_name", "Bônus do Dia"), int(cfg.get("daily_points", 15)))
    dynamic = upsert_campaign(repo, event_date.isoformat(), "dynamic_bonus", cfg.get("dynamic_name", "Bônus Dinâmico"), int(cfg.get("dynamic_points", 20)))
    clear_locations_if_safe(repo, daily["id"])
    clear_locations_if_safe(repo, dynamic["id"])

    tz = ZoneInfo(settings.event_timezone)
    start_dt = datetime.combine(event_date, start, tzinfo=tz)
    end_dt = datetime.combine(event_date, end, tzinfo=tz)

    for zone_slug in REQUIRED_ZONES:
        qr = resolve_qr(repo, str(daily_map[zone_slug]), zone_ids[zone_slug], "daily_bonus")
        repo.insert("bonus_locations", {"campaign_id": daily["id"], "qr_point_id": qr["id"], "zone_id": zone_ids[zone_slug], "starts_at": start_dt.isoformat(), "ends_at": end_dt.isoformat(), "active": True})

    windows = hourly_windows(event_date, start, end, settings.event_timezone)
    for slot_index, (starts_at, ends_at) in enumerate(windows):
        for zone_slug in REQUIRED_ZONES:
            codes = dynamic_map[zone_slug]
            if isinstance(codes, str):
                codes = [codes]
            if not codes:
                raise SystemExit(f"Nenhum QR dinâmico configurado para {zone_slug}.")
            code = str(codes[slot_index % len(codes)])
            qr = resolve_qr(repo, code, zone_ids[zone_slug], "dynamic_bonus")
            repo.insert("bonus_locations", {"campaign_id": dynamic["id"], "qr_point_id": qr["id"], "zone_id": zone_ids[zone_slug], "starts_at": starts_at.isoformat(), "ends_at": ends_at.isoformat(), "active": True})

    logger.info("Bônus configurados para %s: 1 diário + %s janelas dinâmicas, sempre em 3 zonas.", event_date, len(windows))


if __name__ == "__main__":
    main()
