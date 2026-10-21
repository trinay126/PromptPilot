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


def test_config_reports_whether_a_key_is_stored() -> None:
    assert AppConfig().has_api_key is False
    assert AppConfig(api_key="gsk_live_key_value").has_api_key is True


def test_model_info_hides_non_chat_models() -> None:
    from promptpilot.schemas import ModelInfo

    chat = ModelInfo(id="llama-3.3-70b-versatile", output_modalities=["text"])
    assert chat.is_chat_capable is True


def test_model_info_hides_transcription_and_speech_models() -> None:
    from promptpilot.schemas import ModelInfo

    whisper = ModelInfo(id="whisper-large-v3", output_modalities=["transcription"])
    speech = ModelInfo(id="canopylabs/orpheus-v1-english", output_modalities=["speech"])

    assert whisper.is_chat_capable is False
    assert speech.is_chat_capable is False


def test_model_info_hides_text_classification_models() -> None:
    from promptpilot.schemas import ModelInfo

    guard = ModelInfo(id="meta-llama/llama-prompt-guard-2-22m", output_modalities=["text"])

    assert guard.is_chat_capable is False


def test_model_info_keeps_chat_models_that_look_similar() -> None:
    """A safety-tuned chat model is still usable, unlike a classifier."""
    from promptpilot.schemas import ModelInfo

    safeguard = ModelInfo(id="openai/gpt-oss-safeguard-20b", output_modalities=["text"])

    assert safeguard.is_chat_capable is True


def test_model_info_hides_inactive_models() -> None:
    from promptpilot.schemas import ModelInfo

    retired = ModelInfo(id="old-model", output_modalities=["text"], active=False)

    assert retired.is_chat_capable is False


def test_model_info_keeps_models_without_modality_information() -> None:
    from promptpilot.schemas import ModelInfo

    unknown = ModelInfo(id="some-future-model")

    assert unknown.is_chat_capable is True
