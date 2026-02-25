# TODO: добавить эндпоинт PATCH /versions/{version_id}/metrics
# для дозаписи метрик после evaluate (например, после A/B-теста)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.schemas import StageUpdate, VersionResponse

router = APIRouter(prefix="/versions", tags=["versions"])


@router.get("/{version_id}", response_model=VersionResponse)
def get_version(version_id: int, db: Session = Depends(get_db)):
    db_version = crud.get_version_by_id(db, version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    return db_version


@router.patch("/{version_id}/stage", response_model=VersionResponse)
def update_stage(version_id: int, data: StageUpdate, db: Session = Depends(get_db)):
    db_version = crud.get_version_by_id(db, version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Версия не найдена")
    return crud.update_version_stage(db, db_version, data.stage)


@router.delete("/{version_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_version(version_id: int, db: Session = Depends(get_db)):
    # TODO: нельзя удалять production-версию без явного подтверждения.
    # Добавить проверку и заголовок X-Force-Delete
    db_version = crud.get_version_by_id(db, version_id)
    if not db_version:
        raise HTTPException(status_code=404, detail="Версия не найдена.")
    crud.delete_version(db, db_version)
