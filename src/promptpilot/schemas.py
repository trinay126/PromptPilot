"""Pydantic schemas for configuration, requests, responses, and statistics."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from promptpilot.constants import DEFAULT_MODEL, DEFAULT_TIMEOUT_SECONDS

Role = Literal["system", "user", "assistant"]

class Chat