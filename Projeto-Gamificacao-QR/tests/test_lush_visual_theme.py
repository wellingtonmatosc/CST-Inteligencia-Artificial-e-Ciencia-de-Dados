from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_global_theme_uses_single_institutional_hierarchy():
    text = read("app/static/js/common.js")
    mobile = "/static/css/mobile-first.css"
    institutional = "/static/css/theme-institutional.css"
    admin = "/static/css/theme-institutional-admin.css"
    assert mobile in text
    assert institutional in text
    assert admin in text
    assert text.index(mobile) < text.index(institutional)
    assert "theme-lush.css" not in text
    assert "theme-lush-admin.css" not in text
    assert "theme-gradient.css" not in text


def test_institutional_palette_is_clear_and_has_no_green_dependency():
    text = read("app/static/css/theme-institutional.css").lower()
    for color in ("#f6f7fa", "#ffffff", "#062f4f", "#813772", "#b82601"):
        assert color in text
    assert "nenhum tom de verde" in text


def test_public_ranking_has_avatar_podium_and_readable_metrics():
    text = read("app/static/js/ranking.js")
    html = read("app/static/pages/ranking.html")
    assert 'data-position=' in text
    assert "rank-avatar" in text
    assert "avatar_key" in text
    assert "podium-label first" in text
    assert "podium-label second" in text
    assert "podium-label third" in text
    assert "Ouro • 1º lugar" in text
    assert "Prata • 2º lugar" in text
    assert "Bronze • 3º lugar" in text
    assert "rank-metrics" in text
    assert "rank-score-pill" in text
    assert "QRs distintos" in text
    assert "/static/js/avatars.js" in html


def test_ranking_uses_static_metallic_podium_and_reduced_motion():
    public_theme = read("app/static/css/ranking-optimized.css").lower()
    admin_theme = read("app/static/css/theme-institutional-admin.css").lower()
    for color in ("#d4af37", "#aeb7c0", "#b87333"):
        assert color in public_theme
        assert color in admin_theme
    assert "animation:none!important" in public_theme
    assert "backdrop-filter:none!important" in public_theme
    assert "@keyframes" not in public_theme
    assert "@keyframes" not in admin_theme
    assert "a11y-reduced-motion" in public_theme
    assert "prefers-reduced-motion:reduce" in public_theme


def test_ranking_explanatory_text_can_be_collapsed():
    html = read("app/static/pages/ranking.html")
    assert 'class="ranking-info"' in html
    assert "<summary>Ver critérios do ranking</summary>" in html
    assert "/static/css/ranking-optimized.css" in html


def test_mobile_accessibility_control_is_compact():
    text = read("app/static/css/theme-institutional.css")
    assert ".a11y-toggle{width:46px!important" in text
    assert '.a11y-toggle::before{content:"Aa"' in text
