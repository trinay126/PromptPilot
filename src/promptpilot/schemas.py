"""Pydantic schemas for configuration, requests, responses, and statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from promptpilot.constants import DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS

Role = Literal["system", "user", "assistant"]

class ChatMessage(BaseModel):
    """A message accepted by groq's chat-completons API."""
    model_config = ConfigDict(extra="ignore")

    role : Role
    content : Annotated[str, Field(min_length=1, max_lenght=100_000)]

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("message content cannot be blank")
        return cleaned

class chatRequest(BaseModel):
    """Validated request body sent to the Groq REST endpoint."""
    model_config = ConfigDict(extra="forbid")

    model: str = Field(default=DEFAULT_MODEL, min_length=2, max_length=200) 
    messages: list[ChatMessage] = Field(min_length=1, max_length=100)
    temparature: float = Field(default=0.2, ge=0.0, le=2.0)
    max_completion_tokens: int = Field(default=512, gt=0, le=8192)
    stream: bool = False

class ChoiceMessage(BaseModel):
    """Assistant message nested inside one completion choice."""

    model_config = ConfigDict(extra="ignore")

    role: Literal["assistant", "system", "user"]
    content: str

class Choice(BaseModel):
    """One candidate response from the API."""

    model_config = ConfigDict(extra="ignore")

    index: int = 0
    message: ChoiceMessage
    finish_reason: str | None = None

class Usage(BaseModel):
    """Token counters returned by the API when available."""

    model_config = ConfigDict(extra="ignore")

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResoonse(BaseModel):
    """validated non-streaming completion response."""

    model_config = ConfigDict(extra="ignore")

    id: str
    object: str = "chat.completion"
    created: int | None = None
    model: str
    choices: list[Choice] = Field(min_length=1)
    usage: Usage | None = None

    @property
    def text(self) -> str:
        """Return the first assistant message as plain text."""
        return self.choices[0].message.content.strip()

class ModelInfo(BaseModel):
    """One item from the live models endpoint."""

    model_config = ConfigDict(extra="ignore")

    id: str
    object: str = "model"
    owned_by: str | None = None

class ModelListResponse(BaseModel):
    """Response envelope for the models endpoint."""

    model_config = ConfigDict(extra="ignore")

    object: str = "list"
    data: list[ModelInfo] = Field(default_factory=list)


