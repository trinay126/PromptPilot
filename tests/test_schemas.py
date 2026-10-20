import pytest
from pydantic import ValidationError

from promptpilot.schemas import (
    AppConfig,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    Choice,
    ChoiceMessage,
    Usage,
)


def test_message_strips_content() -> None:
    message = ChatMessage(role="user", content="  hello  ")
    assert message.content == "hello"


def test_blank_content_is_rejected() -> None:
    with pytest.raises(ValidationError):
        ChatMessage(role="user", content="   ")


def test_request_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(messages=[ChatMessage(role="user", content="hello")], unknown=True)


def test_request_requires_at_least_one_message() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(messages=[])


def test_request_rejects_out_of_range_temperature() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            messages=[ChatMessage(role="user", content="hello")],
            temperature=2.5,
        )


def test_request_rejects_non_positive_token_budget() -> None:
    with pytest.raises(ValidationError):
        ChatRequest(
            messages=[ChatMessage(role="user", content="hello")],
            max_completion_tokens=0,
        )


def test_response_exposes_first_message_text() -> None:
    response = ChatResponse(
        id="test-id",
        model="test-model",
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content="  Hello  "),
                finish_reason="stop",
            )
        ],
        usage=Usage(prompt_tokens=3, completion_tokens=5, total_tokens=8),
    )

    assert response.text == "Hello"
    assert response.total_tokens == 8


def test_response_without_usage_reports_zero_tokens() -> None:
    response = ChatResponse(
        id="test-id",
        model="test-model",
        choices=[
            Choice(
                index=0,
                message=ChoiceMessage(role="assistant", content="Hello"),
            )
        ],
    )

    assert response.total_tokens == 0


def test_config_normalises_blank_api_key_to_none() -> None:
    assert AppConfig(api_key="   ").api_key is None
    assert AppConfig(api_key=" gsk_live ").api_key == "gsk_live"


def test_config_reports_remaining_demo_prompts() -> None:
    config = AppConfig(demo_limit=5, demo_prompts_used=2)
    assert config.demo_prompts_remaining == 3
    assert AppConfig(demo_limit=5, demo_prompts_used=9).demo_prompts_remaining == 0
