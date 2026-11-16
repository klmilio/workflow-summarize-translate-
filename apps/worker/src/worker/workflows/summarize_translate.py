from pydantic import BaseModel, Field

import mistralai.workflows as workflows
from mistralai.workflows import Depends
from mistralai.workflows.client import get_mistral_client

DEFAULT_MODEL = "mistral-large-latest"


def _message_text(content) -> str:
    if isinstance(content, str):
        return content
    parts = []
    for part in content:
        if isinstance(part, dict):
            if part.get("type") == "text":
                parts.append(part.get("text", ""))
        elif getattr(part, "type", None) == "text":
            parts.append(getattr(part, "text", "") or "")
    return "".join(parts)


class SummarizeTranslateInput(BaseModel):
    text: str = Field(..., description="The text to summarize.")
    max_sentences: int = Field(3, ge=1, le=10, description="Maximum number of sentences in the summary.")


class SummarizeTranslateOutput(BaseModel):
    summary: str
    summary_english: str


@workflows.activity()
async def summarize_text(text: str, max_sentences: int, client=Depends(get_mistral_client)) -> str:
    response = await client.chat.complete_async(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a precise summarizer. Summarize the user's text in 2 to "
                    f"{max_sentences} sentences, in the same language as the text. "
                    "Return only the summary, without any commentary."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    return _message_text(response.choices[0].message.content)


@workflows.activity()
async def translate_to_english(text: str, client=Depends(get_mistral_client)) -> str:
    response = await client.chat.complete_async(
        model=DEFAULT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional translator. Translate the user's text into English. "
                    "Return only the translation, without any commentary."
                ),
            },
            {"role": "user", "content": text},
        ],
    )
    return _message_text(response.choices[0].message.content)


@workflows.workflow.define(
    name="summarize-and-translate",
    workflow_display_name="Summarize and Translate",
    workflow_description="Summarizes the input text in 2-3 sentences, then translates the summary into English.",
)
class SummarizeTranslateWorkflow:
    @workflows.workflow.entrypoint
    async def run(self, input: SummarizeTranslateInput) -> SummarizeTranslateOutput:
        summary = await summarize_text(input.text, input.max_sentences)
        summary_english = await translate_to_english(summary)
        return SummarizeTranslateOutput(summary=summary, summary_english=summary_english)
