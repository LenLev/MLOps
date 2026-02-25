# TODO: добавить логирование операций
# TODO: добавить оптимистичную блокировку при смене стадии версии, чтобы избежать гонки при одновременных PATCH-запросах

from __future__ import annotations
import json
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import Optional, Tuple, List
from app import models
from app.schemas import ModelCreate, ModelUpdate, StageEnum, VersionCreate


def create_model(db: Session, data: ModelCreate) -> models.Model:
    db_model = models.Model(
        name=data.name,
        team=data.team,
        description=data.description,
        tags=json.dumps(data.tags, ensure_ascii=False),
    )
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model


def get_model_by_id(db: Session, model_id: int) -> Optional[models.Model]:
    return db.query(models.Model).filter(models.Model.id == model_id).first()


def get_model_by_name(db: Session, name: str) -> Optional[models.Model]:
    return db.query(models.Model).filter(models.Model.name == name).first()


def list_models(db: Session, team: Optional[str] = None, tag: Optional[str] = None, skip: int = 0, limit: int = 50) -> Tuple[int, List[models.Model]]:
    # TODO: для большого числа моделей добавить полнотекстовый поиск
    q = db.query(models.Model)

    if team:
        q = q.filter(models.Model.team == team)

    if tag:
        q = q.filter(models.Model.tags.like(f'%"{tag}"%'))

    total = q.with_entities(func.count()).scalar()
    items = q.order_by(models.Model.created_at.desc()).offset(skip).limit(limit).all()
    return total, items


def update_model(
    db: Session,
    db_model: models.Model,
    data: ModelUpdate,
) -> models.Model:
    if data.description is not None:
        db_model.description = data.description
    if data.tags is not None:
        db_model.tags = json.dumps(data.tags, ensure_ascii=False)
    db.commit()
    db.refresh(db_model)
    return db_model


def delete_model(db: Session, db_model: models.Model) -> None:
    db.delete(db_model)
    db.commit()


def create_version(db: Session, model_id: int, data: VersionCreate) -> models.ModelVersion:
    if data.stage == StageEnum.production:
        _archive_current_production(db, model_id)

    db_version = models.ModelVersion(
        model_id=model_id,
        version=data.version,
        path=data.path,
        stage=data.stage.value,
        metrics=json.dumps(data.metrics, ensure_ascii=False),
        tags=json.dumps(data.tags, ensure_ascii=False),
        description=data.description,
    )
    db.add(db_version)
    db.commit()
    db.refresh(db_version)
    return db_version


def get_version_by_id(db: Session, version_id: int) -> models.ModelVersion | None:
    return db.query(models.ModelVersion).filter(models.ModelVersion.id == version_id).first()


def list_versions(db: Session, model_id: int) -> List[models.ModelVersion]:
    return (
        db.query(models.ModelVersion)
        .filter(models.ModelVersion.model_id == model_id)
        .order_by(models.ModelVersion.created_at.desc())
        .all()
    )


def get_latest_version(db: Session, model_id: int, stage: StageEnum = StageEnum.production) -> Optional[models.ModelVersion]:
    return (
        db.query(models.ModelVersion)
        .filter(models.ModelVersion.model_id == model_id, models.ModelVersion.stage == stage.value)
        .order_by(models.ModelVersion.created_at.desc())
        .first()
    )


def update_version_stage(db: Session, db_version: models.ModelVersion, new_stage: StageEnum) -> models.ModelVersion:
    # TODO: добавить событие в журнал изменени
    if new_stage == StageEnum.production:
        _archive_current_production(db, db_version.model_id, exclude_id=db_version.id)

    db_version.stage = new_stage.value
    db.commit()
    db.refresh(db_version)
    return db_version


def delete_version(db: Session, db_version: models.ModelVersion) -> None:
    db.delete(db_version)
    db.commit()

def _archive_current_production(
    db: Session,
    model_id: int,
    exclude_id: Optional[int] = None,
) -> None:

    q = db.query(models.ModelVersion).filter(
        models.ModelVersion.model_id == model_id,
        models.ModelVersion.stage == StageEnum.production.value,
    )
    if exclude_id is not None:
        q = q.filter(models.ModelVersion.id != exclude_id)

    q.update({"stage": StageEnum.archived.value}, synchronize_session="fetch")
    db.flush()
