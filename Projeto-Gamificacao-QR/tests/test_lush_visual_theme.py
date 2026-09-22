from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_global_theme_loads_after_mobile_overrides():
    text = read("app/static/js/common.js")
    assert "/static/css/theme-lush.css" in text
    assert "/static/css/theme-lush-admin.css" in text
    assert text.index("/static/css/mobile-first.css") < text.index("/static/css/theme-lush.css")
    assert text.index("/static/css/theme-lush.css") < text.index("/static/css/theme-lush-admin.css")


def test_approved_palette_is_present():
    text = read("app/static/css/theme-lush.css").lower()
    for color in ("#000000", "#062f4f", "#813772", "#b82601"):
        assert color in text


def test_public_ranking_has_podium_and_readable_metrics():
    text = read("app/static/js/ranking.js")
    assert 'data-position=' in text
    assert "podium-label first" in text
    assert "podium-label second" in text
    assert "podium-label third" in text
    assert "rank-metrics" in text
    assert "QRs distintos" in text


def test_podium_effects_respect_reduced_motion():
    public_theme = read("app/static/css/theme-lush.css")
    admin_theme = read("app/static/css/theme-lush-admin.css")
    assert "@keyframes first-breathe" in public_theme
    assert "@keyframes rank-shine" in public_theme
    assert "a11y-reduced-motion" in public_theme
    assert "prefers-reduced-motion:reduce" in public_theme
    assert "@keyframes admin-leader-breathe" in admin_theme
    assert "@keyframes admin-rank-shine" in admin_theme
    assert "a11y-reduced-motion" in admin_theme
    assert "prefers-reduced-motion:reduce" in admin_theme


def test_mobile_accessibility_control_is_compact():
    text = read("app/static/css/theme-lush.css")
    assert ".a11y-toggle{width:48px!important" in text
    assert '.a11y-toggle::before{content:"Aa"' in text
