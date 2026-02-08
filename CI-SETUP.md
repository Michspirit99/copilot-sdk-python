# CI Setup

This repo contains runnable Copilot SDK sample scripts. In CI, we **do not run** the scripts end-to-end because they require:

- GitHub Copilot CLI availability and authentication
- Network access
- Potentially premium model usage depending on your Copilot plan

Instead, CI validates that the repository stays healthy for contributors.

## What CI does

The workflow in [.github/workflows/ci.yml](.github/workflows/ci.yml) runs:

1. **Dependency install** (`pip install -r requirements.txt`)
2. **Environment verification** (`pip check`)
3. **Static compile check** (`python -m compileall samples`)
4. **Import smoke tests** (imports each script under `samples/` to ensure there are no missing top-level dependencies)

## Local equivalent

From repo root:

- Create/activate a venv
- `pip install -r requirements.txt`
- `python -m compileall samples`
- `pytest -q`

## Running samples for real

To run the samples end-to-end locally, you’ll need:

- Copilot CLI installed and authenticated (`copilot auth login`)
- For the Playwright sample: `python -m playwright install chromium`

## Optional CI proof (E2E)

If you want CI to run real networked scenarios as proof, use the manual workflow in [.github/workflows/agent-scenarios.yml](.github/workflows/agent-scenarios.yml).

It supports two modes:

1) `provider=copilot` (unattended Copilot models)

The Copilot SDK client supports non-interactive auth via a GitHub token. Configure this repository secret:

- `COPILOT_GITHUB_TOKEN`

This should be a token that can authenticate as a user with access to Copilot models in your org/account (for example, a PAT/fine-grained token depending on your GitHub policies).

1) `provider=openai` (BYOK)

Configure this repository secret:

- `OPENAI_API_KEY`

Optional:

- `OPENAI_BASE_URL` (defaults to `https://api.openai.com/v1`)

The workflow uploads an `agent-scenarios.txt` transcript as an artifact.
