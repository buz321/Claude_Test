"""요청/응답 스키마."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

Repeat = Literal["none", "daily", "weekly", "monthly"]


def _blank_to_none(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    note: str = ""
    assignee: str = ""
    due_date: str | None = None  # YYYY-MM-DD
    due_time: str | None = None  # HH:MM
    repeat: Repeat = "none"

    @field_validator("due_date", "due_time", mode="before")
    @classmethod
    def _empty(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class TaskPatch(BaseModel):
    title: str | None = None
    note: str | None = None
    assignee: str | None = None
    due_date: str | None = None
    due_time: str | None = None
    repeat: Repeat | None = None
    done: bool | None = None


class ShoppingIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    quantity: str = ""
    note: str = ""
    urgent: bool = False


class ShoppingPatch(BaseModel):
    name: str | None = None
    quantity: str | None = None
    note: str | None = None
    urgent: bool | None = None
    bought: bool | None = None


class EventIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: str  # YYYY-MM-DD
    start_time: str | None = None
    end_time: str | None = None
    location: str = ""
    note: str = ""

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def _empty(cls, value: str | None) -> str | None:
        return _blank_to_none(value)


class EventPatch(BaseModel):
    title: str | None = None
    date: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    location: str | None = None
    note: str | None = None
