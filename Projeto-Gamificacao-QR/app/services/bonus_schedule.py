"""Planejamento das janelas de bônus sem depender dos locais físicos exatos."""
from __future__ import annotations
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

REQUIRED_ZONES = ("cantina", "terreo", "primeiro-andar")


def hourly_windows(event_date: date, start: time, end: time, timezone_name: str) -> list[tuple[datetime, datetime]]:
    tz = ZoneInfo(timezone_name)
    current = datetime.combine(event_date, start, tzinfo=tz)
    finish = datetime.combine(event_date, end, tzinfo=tz)
    if finish <= current:
        raise ValueError("O horário final deve ser posterior ao inicial.")
    windows=[]
    while current < finish:
        nxt=min(current+timedelta(hours=1), finish)
        windows.append((current,nxt))
        current=nxt
    return windows


def validate_zone_mapping(mapping: dict[str, list[str] | str]) -> None:
    missing=[z for z in REQUIRED_ZONES if z not in mapping or not mapping[z]]
    if missing:
        raise ValueError("Faltam alternativas equivalentes nas zonas: " + ", ".join(missing))
