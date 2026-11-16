# summarize-translate-workflow

Mistral Workflow that takes a text, summarizes it in 2-3 sentences, and then translates the summary into English.

## Workflow

`summarize-and-translate` (`apps/worker/src/worker/workflows/summarize_translate.py`):

- **Input**: `{"text": "...", "max_sentences": 3}` (`max_sentences` optional, 1-10, default 3)
- **Steps** (each a durable activity calling the Mistral API via `get_mistral_client()`):
  1. `summarize_text` — summarizes the text in 2-`max_sentences` sentences, in the text's language
  2. `translate_to_english` — translates the summary into English
- **Output**: `{"summary": "...", "summary_english": "..."}`

## Local development

```bash
cd apps/worker
pip install -e ".[dev]"
cp ../.env.example ../.env  # set MISTRAL_API_KEY in .env
python -m pytest                       # local tests on an in-memory Temporal test server
python -m worker.entrypoints.worker     # run the worker locally
```

## Managed deployment

The repository is built as-is by Mistral Cloud; the image entrypoint starts the worker:

- Build directory: repository root
- Dockerfile: `deploy/docker/Dockerfile.worker`

The platform injects `DEPLOYMENT_NAME`, `SERVER_URL` and the service-account token (`MISTRAL_SA_TOKEN_PATH`); no API key is stored in the repo. The worker image installs `mistralai-workflows>=3.10`.

## Run it

```bash
curl -X POST https://api.mistral.ai/v1/workflows/summarize-and-translate/execute \
  -H "Authorization: Bearer $MISTRAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": {"text": "Το κείμενό σου εδώ."}, "wait_for_result": true}'
```
