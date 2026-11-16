import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError
from mistralai.workflows.core.dependencies.dependency_injector import DependencyInjector
from mistralai.workflows.testing import create_test_worker

from worker.workflows.summarize_translate import (
    SummarizeTranslateInput,
    SummarizeTranslateWorkflow,
    get_mistral_client,
    summarize_text,
    translate_to_english,
)

TASK_QUEUE = "test-task-queue"


def _chat_response(content: str) -> MagicMock:
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def fake_mistral_client():
    snapshot = DependencyInjector.snapshot_dependencies()
    client = MagicMock()
    client.chat.complete_async = AsyncMock()

    @asynccontextmanager
    async def fake_get_mistral_client():
        yield client

    DependencyInjector.restore_dependencies({**snapshot, get_mistral_client: fake_get_mistral_client})
    yield client
    DependencyInjector.restore_dependencies(snapshot)


async def test_summarize_then_translate(temporal_env_with_converter, fake_mistral_client):
    fake_mistral_client.chat.complete_async.side_effect = [
        _chat_response("Περίληψη στα ελληνικά."),
        _chat_response("Summary in English."),
    ]

    async with create_test_worker(
        temporal_env_with_converter,
        [SummarizeTranslateWorkflow],
        activities=[summarize_text, translate_to_english],
        task_queue=TASK_QUEUE,
    ):
        result = await temporal_env_with_converter.client.execute_workflow(
            SummarizeTranslateWorkflow.run,
            SummarizeTranslateInput(text="Ένα αρκετά μακρύ κείμενο προς σύνοψη.", max_sentences=3),
            id=f"test-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )

    assert result["summary"] == "Περίληψη στα ελληνικά."
    assert result["summary_english"] == "Summary in English."
    assert fake_mistral_client.chat.complete_async.await_count == 2
    translate_call = fake_mistral_client.chat.complete_async.await_args_list[1]
    assert translate_call.kwargs["messages"][-1]["content"] == "Περίληψη στα ελληνικά."


def test_max_sentences_validation():
    with pytest.raises(ValidationError):
        SummarizeTranslateInput(text="κείμενο", max_sentences=0)
    with pytest.raises(ValidationError):
        SummarizeTranslateInput(text="κείμενο", max_sentences=11)
