"""Tests for the interactive model picker."""

from promptpilot.picker import filter_models, group_by_owner
from promptpilot.schemas import ModelInfo


def models() -> list[ModelInfo]:
    """Build a small catalog covering several owners."""
    return [
        ModelInfo(id="openai/gpt-oss-120b", owned_by="OpenAI"),
        ModelInfo(id="openai/gpt-oss-20b", owned_by="OpenAI"),
        ModelInfo(id="meta-llama/llama-3.3-70b-versatile", owned_by="Meta"),
        ModelInfo(id="canopylabs/orpheus-v1-english", owned_by="Canopy Labs"),
        ModelInfo(id="qwen/qwen3.8-27b", owned_by="Alibaba Cloud"),
    ]


def test_group_by_owner_sorts_owners_and_models() -> None:
    groups = group_by_owner(models())

    assert [owner for owner, _ in groups] == [
        "Alibaba Cloud",
        "Canopy Labs",
        "Meta",
        "OpenAI",
    ]
    openai = next(group for owner, group in groups if owner == "OpenAI")
    assert [model.id for model in openai] == [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]


def test_group_by_owner_handles_a_missing_owner() -> None:
    groups = group_by_owner([ModelInfo(id="orphan-model")])

    assert groups[0][0] == "unknown"


def test_filter_models_with_an_empty_query_returns_everything() -> None:
    groups = group_by_owner(models())

    assert len(filter_models(groups, "")) == 5
    assert len(filter_models(groups, "   ")) == 5


def test_filter_models_matches_a_substring() -> None:
    groups = group_by_owner(models())

    matches = filter_models(groups, "gpt")

    assert [model.id for model in matches] == [
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
    ]


def test_filter_models_is_case_insensitive() -> None:
    groups = group_by_owner(models())

    assert len(filter_models(groups, "GPT-OSS")) == 2


def test_filter_models_requires_every_word() -> None:
    groups = group_by_owner(models())

    assert filter_models(groups, "openai safeguard") == []
    assert len(filter_models(groups, "openai oss")) == 2


def test_filter_models_returns_nothing_for_a_non_match() -> None:
    groups = group_by_owner(models())

    assert filter_models(groups, "definitely-not-a-model") == []
