from app.services.scoring import (
    milestone_points,
    normal_max_attempts,
    normal_participation_points,
    normal_score_for_attempt,
    score_for_attempt,
)


def test_generic_score_for_attempts_is_preserved_for_bonus_flows():
    assert score_for_attempt(10, 1) == 10
    assert score_for_attempt(10, 2) == 7
    assert score_for_attempt(10, 3) == 5
    assert score_for_attempt(10, 4) == 0


def test_normal_true_false_has_single_attempt():
    assert normal_max_attempts("true_false") == 1


def test_other_normal_questions_have_two_attempts():
    assert normal_max_attempts("multiple_choice") == 2
    assert normal_max_attempts("short_text") == 2
    assert normal_max_attempts("association") == 2
    assert normal_max_attempts("ordering") == 2


def test_normal_scoring_is_10_then_6():
    assert normal_score_for_attempt(1) == 10
    assert normal_score_for_attempt(2) == 6
    assert normal_score_for_attempt(3) == 0


def test_normal_participation_is_two_points():
    assert normal_participation_points() == 2


def test_daily_milestones_are_cumulative():
    assert milestone_points(2) == []
    assert milestone_points(3) == [(3, 5)]
    assert milestone_points(5) == [(3, 5), (5, 10)]
