# TODO: если понадобится фильтрация по тегам на уровне SQL- вынести tags в отдельную таблицу many-to-many.

import json
from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    team = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True, default="[]")
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    versions = relationship(
        "ModelVersion",
        back_populates="model",
        cascade="all, delete-orphan",
        order_by="ModelVersion.created_at",
    )

    def tags_list(self):
        try:
            return json.loads(self.tags or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def __repr__(self) -> str:
        return f"<Model id={self.id} name={self.name!r} team={self.team!r}>"


class ModelVersion(Base):
    # TODO: добавить индекс на (model_id, stage) для быстрого поиска
    #       актуальной production-версии при большом числе версий.
    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(64), nullable=False)
    path = Column(Text, nullable=False)
    stage = Column(String(32), nullable=False, default="staging")
    metrics = Column(Text, nullable=True, default="{}")
    tags = Column(Text, nullable=True, default="[]")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_now)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    model = relationship("Model", back_populates="versions")

    def metrics_dict(self):
        try:
            return json.loads(self.metrics or "{}")
        except (json.JSONDecodeError, TypeError):
            return {}

    def tags_list(self):
        try:
            return json.loads(self.tags or "[]")
        except (json.JSONDecodeError, TypeError):
            return []

    def __repr__(self) -> str:
        return f"<ModelVersion id={self.id} model_id={self.model_id} version={self.version!r} stage={self.stage!r}>"
