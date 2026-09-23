"""Asynchronous Groq REST client and gather - based batch execution."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable

import httpx

from promptpilot.constants import GROQ_BASE_URL
from promptpilot.decorators import async_retry_on_api_error
from promptpilot.exceptions import GroqAPIError, SchemaError
from promptpilot.schemas import ChatMessage, ChatRequest, ChatResponse, ModelListResponse
