"""Phase 5: curriculum and lesson content endpoints."""

import pytest
from fastapi import HTTPException

from app.api.v1.routes.content import get_curriculum, get_lesson


def test_curriculum_lists_family_with_available_and_planned_concepts():
    curriculum = get_curriculum()

    families = curriculum["families"]
    assert [family["id"] for family in families] == ["separation_fundamentals"]
    concepts = {concept["id"]: concept for concept in families[0]["concepts"]}
    assert concepts["traffic_relationships"]["status"] == "available"
    assert concepts["vertical_separation"]["status"] == "planned"
    assert concepts["horizontal_separation"]["status"] == "planned"
    # Planned groups stay lightweight: outline metadata only, no lessons.
    assert "lessons" not in concepts["horizontal_separation"]
    journey = [
        entry["lesson_id"]
        for entry in concepts["traffic_relationships"]["lessons"]
    ]
    assert journey == [
        "tr_understanding_track",
        "tr_same_track",
        "tr_reciprocal_track",
        "tr_crossing_track",
        "tr_identify_relationship",
    ]


def test_lesson_endpoint_returns_steps_with_translation_keys():
    payload = get_lesson("training_alpha", "tr_same_track")

    lesson = payload["lesson"]
    assert lesson["id"] == "tr_same_track"
    step_types = [step["type"] for step in lesson["lesson_steps"]]
    assert step_types[0] == "observe"
    assert "classify" in step_types
    assert step_types[-1] == "complete"
    first_step = lesson["lesson_steps"][0]
    assert first_step["scenario_id"] == "tr_same_track"
    assert first_step["text_key"].startswith("lessons.tr_same_track.")
    classify_step = next(s for s in lesson["lesson_steps"] if s["type"] == "classify")
    assert classify_step["options"] == [
        "same_track",
        "reciprocal_track",
        "crossing_track",
        "neither",
    ]


def test_identify_lesson_examples_reference_their_scenarios():
    payload = get_lesson("training_alpha", "tr_identify_relationship")
    examples = [
        step
        for step in payload["lesson"]["lesson_steps"]
        if step["type"] == "classify"
    ]
    assert [step["scenario_id"] for step in examples] == [
        "tr_same_track",
        "tr_reciprocal_track",
        "tr_crossing_track",
        "tr_identify_diverging",
        "tr_identify_deceptive",
    ]


def test_unknown_lesson_returns_404():
    with pytest.raises(HTTPException) as exc_info:
        get_lesson("training_alpha", "no_such_lesson")
    assert exc_info.value.status_code == 404
