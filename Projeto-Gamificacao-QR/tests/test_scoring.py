from app.services.scoring import milestone_points, score_for_attempt


def test_score_for_attempts():
    assert score_for_attempt(10, 1) == 10
    assert score_for_attempt(10, 2) == 7
    assert score_for_attempt(10, 3) == 5
    assert score_for_attempt(10, 4) == 0


def test_daily_milestones_are_cumulative():
    assert milestone_points(2) == []
    assert milestone_points(3) == [(3, 5)]
    assert milestone_points(5) == [(3, 5), (5, 10)]
