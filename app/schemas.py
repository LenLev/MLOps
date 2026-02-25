from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

class StageEnum(str, Enum):
    staging = "staging"
    production = "production"
    archived = "archived"

class ModelCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    team: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    tags: List[str] = Field(default=[])

class ModelUpdate(BaseModel):
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    # TODO: добавить возможность перевода модели в архив целиком (без удаления

class ModelResponse(BaseModel):
    id: int
    name: str
    team: str
    description: Optional[str]
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v or []

class ModelListResponse(BaseModel):
    total: int
    items: List[ModelResponse]

class VersionCreate(BaseModel):
    version: str = Field(..., min_length=1, max_length=64)
    path: str = Field(..., min_length=1)
    stage: StageEnum = Field(StageEnum.staging)
    metrics: Dict[str, Any] = Field(default={})
    tags: List[str] = Field(default=[])
    description: Optional[str] = None

class StageUpdate(BaseModel):
    stage: StageEnum

class VersionResponse(BaseModel):
    id: int
    model_id: int
    version: str
    path: str
    stage: StageEnum
    metrics: Dict[str, Any]
    tags: List[str]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True, "protected_namespaces": ()}

    @field_validator("metrics", mode="before")
    @classmethod
    def parse_metrics(cls, v: Any) -> Dict:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v or {}

    @field_validator("tags", mode="before")
    @classmethod
    
    def parse_tags(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v or []
