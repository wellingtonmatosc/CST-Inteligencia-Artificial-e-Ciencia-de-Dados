from app.services.questions import evaluate_answer, normalize_text, validate_accessibility_metadata


def test_short_text_normalization():
    q={"kind":"short_text","correct_answer":{"accepted":["Cuiabá"]}}
    assert evaluate_answer(q,"  CUIABA ") is True


def test_multiple_choice():
    q={"kind":"multiple_choice","correct_answer":{"value":"A"}}
    assert evaluate_answer(q,"A") is True
    assert evaluate_answer(q,"B") is False


def test_image_requires_alt_text():
    q={"media_type":"image","accessibility":{"instructions_clear":True,"depends_on_color_only":False,"requires_speed":False}}
    assert validate_accessibility_metadata(q)
    q["accessibility"]["alt_text"]="Descrição equivalente"
    assert validate_accessibility_metadata(q)==[]


def test_question_cannot_require_speed_or_color_only():
    q={"media_type":None,"accessibility":{"instructions_clear":True,"depends_on_color_only":True,"requires_speed":True}}
    issues=validate_accessibility_metadata(q)
    assert len(issues)==2


def test_normalize_text_removes_accents_and_extra_space():
    assert normalize_text("  Mato   Grósso ")=="mato grosso"
