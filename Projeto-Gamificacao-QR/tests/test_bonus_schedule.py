from datetime import date, time
import pytest
from app.services.bonus_schedule import hourly_windows, validate_zone_mapping


def test_hourly_windows_cover_full_period():
    windows=hourly_windows(date(2026,9,5),time(7,0),time(10,30),"America/Cuiaba")
    assert len(windows)==4
    assert windows[0][0].hour==7
    assert windows[-1][1].hour==10 and windows[-1][1].minute==30


def test_three_accessible_zones_are_required():
    validate_zone_mapping({"cantina":"A","terreo":"B","primeiro-andar":"C"})
    with pytest.raises(ValueError):
        validate_zone_mapping({"cantina":"A","terreo":"B"})
