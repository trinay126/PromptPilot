"""Synchronous Groq REST Client with JSON and SSE Streaming support."""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Iterator

import httpx

from promptpilot.constants import GROQ_BASE_URL
from promptpilot.decorators import retry_on_api_error, timed
from promptpilot.exceptions import GroqAPIError, SchemaError
from promptpilot.schemas import ChatMessage, ChatRequest, ChatResponse, ModelListResponse

