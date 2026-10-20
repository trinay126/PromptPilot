from pydantic import ValidationError
import pytest

from promptpilot.schemas import ChatMessage, ChatRequest


def test_message_strips_content() -> None:
    message = ChatMessage(role="user", content="  hello  ")
    assert message.content == "hello"


def test_blank_content_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(role="user", content="   ")


def test_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(messages=[ChatMessage(role="user", content="hello")], unknown=True)
