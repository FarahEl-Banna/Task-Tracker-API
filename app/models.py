from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Field, SQLModel


class TaskStatus(str, Enum):
    TODO = "ToDo"
    IN_PROGRESS = "InProgress"
    DONE = "Done"


class TaskPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str = ""
    status: str = TaskStatus.TODO.value
    priority: str = TaskPriority.MEDIUM.value
    assignee: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: Optional[str] = ""
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    assignee: Optional[str] = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: object) -> str:
        if value is None:
            raise ValueError("title is required")
        if not isinstance(value, str):
            raise TypeError("title must be a string")

        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("title cannot be empty")
        if len(cleaned_value) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return cleaned_value


class TaskUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee: Optional[str] = None

    @field_validator("title", mode="before")
    @classmethod
    def validate_title(cls, value: object) -> Optional[str]:
        if value is None:
            return None
        if not isinstance(value, str):
            raise TypeError("title must be a string")

        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("title cannot be empty")
        if len(cleaned_value) > 200:
            raise ValueError("title must be 200 characters or fewer")
        return cleaned_value


class TaskResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee: Optional[str]
    created_at: datetime
    updated_at: datetime
