from pathlib import Path


ROOT = Path(__file__).parents[1]
STATIC = ROOT / "app" / "static"
PAGES = STATIC / "pages"
JS = STATIC / "js"
CSS = STATIC / "css"


def test_all_pages_are_pt_br():
    for name in ("index.html", "ranking.html", "scan.html", "admin.html"):
        text = (PAGES / name).read_text(encoding="utf-8")
        assert 'lang="pt-BR"' in text, f"{name} precisa declarar pt-BR"


def test_mobile_first_stylesheet_precedes_institutional_theme():
    text = (JS / "common.js").read_text(encoding="utf-8")
    mobile = "ensureStylesheet('/static/css/mobile-first.css')"
    theme = "ensureStylesheet('/static/css/theme-institutional.css')"
    assert mobile in text
    assert theme in text
    assert text.index(mobile) < text.index(theme)


def test_high_contrast_final_is_loaded_after_visual_themes():
    text = (JS / "common.js").read_text(encoding="utf-8")
    high_contrast = "ensureStylesheet('/static/css/high-contrast-final.css')"
    theme = "ensureStylesheet('/static/css/theme-institutional.css')"
    ranking = "ensureStylesheet('/static/css/ranking-optimized.css')"
    admin = "ensureStylesheet('/static/css/theme-institutional-admin.css')"
    assert high_contrast in text
    assert text.index(high_contrast) > text.index(theme)
    assert text.index(high_contrast) > text.index(ranking)
    assert text.index(high_contrast) > text.index(admin)


def test_high_contrast_final_covers_core_components():
    text = (CSS / "high-contrast-final.css").read_text(encoding="utf-8")
    for selector in (
        "html.a11y-contrast .a11y-panel",
        "html.a11y-contrast .individual-ranking-card",
        "html.a11y-contrast .progress-grid>div",
        "html.a11y-contrast input:not([type=\"radio\"]):not([type=\"checkbox\"])",
        "html.a11y-contrast .admin-shell .admin-nav button",
    ):
        assert selector in text
    assert "--hc-focus:#ffd54a" in text
    assert "background:#ffffff!important" in text
    assert "color:#000000!important" in text


def test_mobile_first_has_target_breakpoints_and_touch_targets():
    text = (CSS / "mobile-first.css").read_text(encoding="utf-8")
    for breakpoint in ("max-width:359px", "min-width:430px", "min-width:600px", "min-width:900px"):
        assert breakpoint in text
    assert "--mobile-touch:48px" in text
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in text
    assert "overflow-x:hidden" in text


def test_new_theme_covers_narrow_mobile_and_admin_navigation():
    theme = (CSS / "theme-institutional.css").read_text(encoding="utf-8")
    admin = (CSS / "theme-institutional-admin.css").read_text(encoding="utf-8")
    ranking = (CSS / "ranking-optimized.css").read_text(encoding="utf-8")
    assert "@media(max-width:640px)" in theme
    assert "@media(max-width:900px)" in admin
    assert "overflow-x:auto" in admin
    assert "@media(max-width:359px)" in ranking
    assert "text-overflow:ellipsis" in ranking


def test_individual_competition_copy_is_consistent():
    scan = (PAGES / "scan.html").read_text(encoding="utf-8")
    index = (PAGES / "index.html").read_text(encoding="utf-8")
    participant_js = (JS / "index.js").read_text(encoding="utf-8")

    assert "Ranking das equipes" not in scan
    assert "Ranking individual" in scan
    assert "Ler código QR" in index
    assert "Ler código QR" in participant_js
    assert "Apelido (nick)" in index
