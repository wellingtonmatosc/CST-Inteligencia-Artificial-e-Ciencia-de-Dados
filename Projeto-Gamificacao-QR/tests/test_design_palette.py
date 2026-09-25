from __future__ import annotations

import colorsys
import re
from pathlib import Path


CSS_ROOT = Path(__file__).parents[1] / "app" / "static" / "css"
HEX_COLOR = re.compile(r"#([0-9a-fA-F]{3,8})(?![0-9a-fA-F])")
RGB_COLOR = re.compile(r"rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})", re.I)
FORBIDDEN_NAMES = re.compile(
    r"\b(?:green|lime|olive|teal|chartreuse|aquamarine|seagreen|forestgreen|springgreen)\b",
    re.I,
)


def _hex_to_rgb(token: str) -> tuple[int, int, int] | None:
    if len(token) in {3, 4}:
        values = [int(ch * 2, 16) for ch in token[:3]]
        return tuple(values)
    if len(token) in {6, 8}:
        return tuple(int(token[i : i + 2], 16) for i in (0, 2, 4))
    return None


def _is_forbidden_hue(rgb: tuple[int, int, int]) -> bool:
    r, g, b = (channel / 255 for channel in rgb)
    hue, saturation, value = colorsys.rgb_to_hsv(r, g, b)
    hue_degrees = hue * 360
    # Faixa deliberadamente ampla para impedir variantes visualmente próximas.
    return 70 <= hue_degrees <= 170 and saturation >= 0.18 and value >= 0.12


def test_css_palette_does_not_use_forbidden_hues():
    failures: list[str] = []
    for css_file in sorted(CSS_ROOT.glob("*.css")):
        text = css_file.read_text(encoding="utf-8")

        if FORBIDDEN_NAMES.search(text):
            failures.append(f"{css_file.name}: nome de cor proibido")

        for match in HEX_COLOR.finditer(text):
            rgb = _hex_to_rgb(match.group(1))
            if rgb and _is_forbidden_hue(rgb):
                failures.append(f"{css_file.name}: {match.group(0)}")

        for match in RGB_COLOR.finditer(text):
            rgb = tuple(min(255, int(match.group(i))) for i in range(1, 4))
            if _is_forbidden_hue(rgb):
                failures.append(f"{css_file.name}: {match.group(0)})")

    assert not failures, "Paleta visual contém tons proibidos: " + ", ".join(failures)
