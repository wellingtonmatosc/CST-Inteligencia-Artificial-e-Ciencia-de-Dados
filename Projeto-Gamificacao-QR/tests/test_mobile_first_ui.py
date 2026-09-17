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


def test_mobile_first_stylesheet_is_loaded_globally_after_theme():
    text = (JS / "common.js").read_text(encoding="utf-8")
    theme = "ensureStylesheet('/static/css/theme-gradient.css')"
    mobile = "ensureStylesheet('/static/css/mobile-first.css')"
    assert theme in text
    assert mobile in text
    assert text.index(mobile) > text.index(theme)


def test_mobile_first_has_target_breakpoints_and_touch_targets():
    text = (CSS / "mobile-first.css").read_text(encoding="utf-8")
    for breakpoint in ("max-width:359px", "min-width:430px", "min-width:600px", "min-width:900px"):
        assert breakpoint in text
    assert "--mobile-touch:48px" in text
    assert "grid-template-columns:repeat(3,minmax(0,1fr))" in text
    assert "overflow-x:hidden" in text


def test_individual_competition_copy_is_consistent():
    scan = (PAGES / "scan.html").read_text(encoding="utf-8")
    index = (PAGES / "index.html").read_text(encoding="utf-8")
    participant_js = (JS / "index.js").read_text(encoding="utf-8")

    assert "Ranking das equipes" not in scan
    assert "Ranking individual" in scan
    assert "Ler código QR" in index
    assert "Ler código QR" in participant_js
    assert "Apelido (nick)" in index
