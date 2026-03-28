# Markdown + Vapi Onboarding CLI (Python)

This project provides a Python CLI assistant for onboarding conversations about a codebase.

It combines:
- **Local Markdown context** (`docs/context/*.md`) as knowledge base
- **Vapi** for conversational final answers

The CLI runs in Markdown-first mode for grounding: if Markdown context is missing, it asks you to generate/fill docs first.

The assistant is optimized for common onboarding questions:
- what the project is for
- how to build/run it
- architecture/design
- external service integrations

## 1) Prerequisites

- Python 3.10+
- Vapi API key + assistant ID
- For voice mode: `SpeechRecognition` + microphone backend (`PyAudio`) and TTS backend (`pyttsx3` or `spd-say`)

## 2) Configure

1. Copy environment template:

```bash
cp env.example .env
```

2. Fill `.env` values:
- `VAPI_API_KEY`
- `VAPI_ASSISTANT_ID`
- (optional) `VAPI_BASE_URL`, `VAPI_CHAT_PATH`
- (optional) `MARKDOWN_CONTEXT_DIR` (default: `./docs/context`)
- `TARGET_REPO` (recommended; format: `github.com/org/repo`)

## 3) Install

```bash
python -m pip install -e .
```

Then generate base Markdown context files:

```bash
python3 -m onboarding_cli.cli generate-md
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

Voice chat (microphone in, spoken answer out):

```bash
onboarder voice-chat
```

If you have ALSA/JACK warnings, use the default `arecord` path (already default):
- `VOICE_USE_PYAUDIO=false`
- `VOICE_INPUT_DEVICE=default`

You can list ALSA capture devices and set one explicitly:

```bash
arecord -l
```

Then put in `.env`, for example:

```bash
VOICE_INPUT_DEVICE=hw:0,0
```

Show retrieved Markdown context:

```bash
onboarder --show-context ask "What external services are connected?"
```

## Notes on API Compatibility

Vapi integrations can vary by account/setup and endpoint version.
If your Vapi account expects a different payload shape or endpoint, update `onboarding_cli/vapi_client.py` (`generate_answer` method).

## Repository Detection and Safety

The CLI always resolves a target repository and fails fast if it cannot.

- It uses `TARGET_REPO` if set.
- Otherwise it auto-detects from `git remote.origin.url`.
- If neither works, startup fails with `Unknown repository`.
