# TODO: добавить аутентификацию (API-ключ или JWT) сейчас доступ открыт
# TODO: добавить пагинацию курсором (cursor-based) вместо offset для больших коллекций

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app import crud
from app.database import get_db
from app.schemas import ModelCreate, ModelListResponse, ModelResponse, ModelUpdate, StageEnum, VersionCreate, VersionResponse

router = APIRouter(prefix="/models", tags=["models"])


@router.post("", response_model=ModelResponse, status_code=status.HTTP_201_CREATED)
def register_model(data: ModelCreate, db: Session = Depends(get_db)):
    try:
        return crud.create_model(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"Модель '{data.name}' уже существует.")


@router.get("", response_model=ModelListResponse)
def list_models(
    team: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    total, items = crud.list_models(db, team=team, tag=tag, skip=skip, limit=limit)
    return ModelListResponse(total=total, items=items)


@router.get("/{model_id}", response_model=ModelResponse)
def get_model(model_id: int, db: Session = Depends(get_db)):
    db_model = crud.get_model_by_id(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    return db_model


@router.patch("/{model_id}", response_model=ModelResponse)
def update_model(model_id: int, data: ModelUpdate, db: Session = Depends(get_db)):
    db_model = crud.get_model_by_id(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    return crud.update_model(db, db_model, data)


@router.delete("/{model_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model(model_id: int, db: Session = Depends(get_db)):
    # TODO: добавить подтверждение (X-Confirm: delete) для защиты от случайного удаления
    # TODO: реализовать мягкое удаление (soft delete) через флаг is_deleted
    db_model = crud.get_model_by_id(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Модель не найдена")
    crud.delete_model(db, db_model)


@router.post("/{model_id}/versions", response_model=VersionResponse, status_code=status.HTTP_201_CREATED)
def add_version(model_id: int, data: VersionCreate, db: Session = Depends(get_db)):
    db_model = crud.get_model_by_id(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Модель не найдена.")
    return crud.create_version(db, model_id, data)


@router.get("/{model_id}/versions", response_model=List[VersionResponse])
def list_versions(model_id: int, db: Session = Depends(get_db)):
    db_model = crud.get_model_by_id(db, model_id)
    if not db_model:
        raise HTTPException(status_code=404, detail="Модель не найдена.")
    return crud.list_versions(db, model_id)


@router.get("/{model_name}/latest", response_model=VersionResponse)
def get_latest_version(model_name: str, stage: StageEnum = Query(StageEnum.production), db: Session = Depends(get_db)):
    db_model = crud.get_model_by_name(db, model_name)
    if not db_model:
        raise HTTPException(status_code=404, detail=f"Модель '{model_name}' не найдена")

    version = crud.get_latest_version(db, db_model.id, stage)
    if not version:
        raise HTTPException(status_code=404, detail=f"У '{model_name}' нет версий в стадии '{stage}'")
    return version
