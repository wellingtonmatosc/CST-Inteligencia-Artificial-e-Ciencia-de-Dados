from app.api.admin_dashboard import attach_individual_progress


def test_attach_individual_progress_maps_ranking_by_participant_id():
    participants = [
        {"id": "p1", "nick": "Ana", "active": True},
        {"id": "p2", "nick": "Beto", "active": True},
    ]
    ranking = [
        {
            "id": "p1",
            "nick": "Ana",
            "points": 80,
            "position": 2,
            "trails_completed": 1,
            "stations_validated": 3,
        }
    ]

    result = attach_individual_progress(participants, ranking)

    assert result[0]["points"] == 80
    assert result[0]["position"] == 2
    assert result[0]["trails_completed"] == 1
    assert result[0]["stations_validated"] == 3
    assert result[1]["points"] == 0
    assert result[1]["position"] is None
    assert result[1]["trails_completed"] == 0
    assert result[1]["stations_validated"] == 0


def test_attach_individual_progress_does_not_mutate_input():
    participants = [{"id": "p1", "nick": "Ana", "active": True}]
    ranking = [{"id": "p1", "points": 10, "position": 1, "trails_completed": 0, "stations_validated": 1}]

    attach_individual_progress(participants, ranking)

    assert "points" not in participants[0]
    assert "position" not in participants[0]
