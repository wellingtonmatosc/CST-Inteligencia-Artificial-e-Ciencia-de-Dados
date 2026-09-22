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
    assert "Ouro • 1º lugar" in text
    assert "Prata • 2º lugar" in text
    assert "Bronze • 3º lugar" in text
    assert "rank-metrics" in text
    assert "rank-score-pill" in text
    assert "QRs distintos" in text


def test_ranking_uses_lightweight_effects_and_metallic_podium():
    public_theme = read("app/static/css/ranking-optimized.css").lower()
    admin_theme = read("app/static/css/theme-lush-admin.css").lower()
    for color in ("#d4af37", "#aeb7c0", "#b87333"):
        assert color in public_theme
        assert color in admin_theme
    assert "background-attachment:scroll!important" in public_theme
    assert "animation:none!important" in public_theme
    assert "backdrop-filter:none!important" in public_theme
    assert "admin-leader-breathe" not in admin_theme
    assert "admin-rank-shine" not in admin_theme
    assert "a11y-reduced-motion" in public_theme
    assert "prefers-reduced-motion:reduce" in public_theme


def test_ranking_explanatory_text_can_be_collapsed():
    html = read("app/static/pages/ranking.html")
    assert 'class="ranking-info"' in html
    assert "<summary>Ver critérios do ranking</summary>" in html
    assert "/static/css/ranking-optimized.css" in html


def test_mobile_accessibility_control_is_compact():
    text = read("app/static/css/theme-lush.css")
    assert ".a11y-toggle{width:48px!important" in text
    assert '.a11y-toggle::before{content:"Aa"' in text
