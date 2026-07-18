"""Learning-content routes: curriculum and lesson definitions.

Content is public guest-browsable data (no session scoping): the curriculum
drives the Learn catalogue and lesson JSON drives the generic lesson runners,
so adding a lesson requires content + translations only — no new frontend
pages or API changes.
"""

from fastapi import APIRouter, HTTPException, status

from ....airspace_packages import (
    find_manifest_item,
    read_json_object,
    resolve_airspace_package_dir,
    resolve_package_file,
)
from ....paths import CONTENT_ROOT

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/curriculum")
def get_curriculum() -> dict:
    """Return the curriculum (families, concepts, lesson journeys, statuses)."""

    curriculum = read_json_object(CONTENT_ROOT / "curriculum.v1.json")
    if curriculum is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Curriculum content is not available.",
        )
    return curriculum


@router.get("/lessons/{airspace_id}/{lesson_id}")
def get_lesson(airspace_id: str, lesson_id: str) -> dict:
    """Return one lesson definition (steps, scenario references, keys)."""

    try:
        package_dir = resolve_airspace_package_dir(airspace_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    manifest = read_json_object(package_dir / "package.v1.json")
    if manifest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Airspace package not found: {airspace_id}",
        )
    lesson_item = find_manifest_item(manifest, collection="lessons", item_id=lesson_id)
    if lesson_item is None or not isinstance(lesson_item.get("path"), str):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson not found in package: {lesson_id}",
        )
    try:
        lesson_path = resolve_package_file(package_dir, lesson_item["path"])
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    lesson = read_json_object(lesson_path)
    if lesson is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lesson file could not be read: {lesson_item['path']}",
        )
    return {
        "airspace_id": airspace_id,
        "lesson_id": lesson_id,
        "manifest": lesson_item,
        "lesson": lesson,
    }
