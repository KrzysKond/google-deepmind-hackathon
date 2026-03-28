# DeepWiki + Vapi Onboarding CLI (Python)

This project provides a Python CLI assistant for onboarding conversations about a codebase.

It combines:
- **DeepWiki MCP** for repository-aware context (`ask_question` tool)
- **Vapi** for conversational final answers

The assistant is optimized for common onboarding questions:
- what the project is for
- how to build/run it
- architecture/design
- external service integrations

## 1) Prerequisites

- Python 3.10+
- `remote-mcp-cli` available in your shell
- Vapi API key + assistant ID

## 2) Configure

1. Copy environment template:

```bash
cp env.example .env
```

2. Fill `.env` values:
- `VAPI_API_KEY`
- `VAPI_ASSISTANT_ID`
- (optional) `VAPI_BASE_URL`, `VAPI_CHAT_PATH`
- (optional) DeepWiki MCP settings
- (optional) `DEEPWIKI_REPO_NAME` (e.g. `owner/repo`, overrides auto-derived repo name)
- `TARGET_REPO` (recommended; format: `github.com/org/repo`)

3. Copy DeepWiki MCP server config:

```bash
cp mcp_servers.example.json mcp_servers.json
```

## 3) Install

```bash
python -m pip install -e .
```

This installs project dependencies, including `remote-mcp-cli`.
Quick check:

```bash
remote-mcp-cli --help
```

## 4) Usage

Single question:

```bash
onboarder ask "How do I build this project?"
```

Interactive chat:

```bash
onboarder chat
```

Show retrieved DeepWiki context:

```bash
onboarder --show-context ask "What external services are connected?"
```

## Notes on API Compatibility

Vapi and MCP integrations can vary by account/setup and endpoint version.
If your Vapi account expects a different payload shape or endpoint, update `onboarding_cli/vapi_client.py` (`generate_answer` method).

If your DeepWiki MCP tool name or argument shape differs from `ask_question` + `{"question": ...}`, update `onboarding_cli/deepwiki_mcp_client.py`.

## Repository Detection and Safety

The CLI always resolves a target repository and fails fast if it cannot.

- It uses `TARGET_REPO` if set.
- Otherwise it auto-detects from `git remote.origin.url`.
- If neither works, startup fails with `Unknown repository`.
