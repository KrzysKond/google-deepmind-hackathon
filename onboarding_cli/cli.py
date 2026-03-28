from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

from onboarding_cli.assistant import OnboardingAssistant
from onboarding_cli.config import AppConfig, load_config
from onboarding_cli.markdown_context_client import MarkdownContextClient
from onboarding_cli.vapi_client import VapiClient
from onboarding_cli.voice_io import VoiceIO


UX_DELAY_SECONDS = 0.35


def _resolve_repo_identifier_lightweight() -> str:
    explicit = os.getenv("TARGET_REPO", "").strip()
    if explicit:
        return explicit.rstrip("/").removesuffix(".git")

    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return "unknown-repo"

    remote = result.stdout.strip().rstrip("/").removesuffix(".git")
    if not remote:
        return "unknown-repo"
    if "://" in remote:
        return remote.split("://", 1)[1]
    if "@" in remote and ":" in remote:
        host_part = remote.split("@", 1)[1]
        host, path = host_part.split(":", 1)
        return f"{host}/{path}"
    return remote


def _build_assistant(config: AppConfig) -> tuple[OnboardingAssistant, str]:
    context_client = MarkdownContextClient(config.markdown_context_dir)
    vapi_client = VapiClient(
        api_key=config.vapi_api_key,
        base_url=config.vapi_base_url,
        chat_path=config.vapi_chat_path,
        assistant_id=config.vapi_assistant_id,
    )
    assistant = OnboardingAssistant(
        context_client=context_client,
        vapi_client=vapi_client,
        system_context=config.system_context,
    )
    return assistant, config.repo_identifier


def _print_response(assistant: OnboardingAssistant, question: str, show_context: bool) -> str:
    print("\n[assistant] Scanning local Markdown context...")
    time.sleep(UX_DELAY_SECONDS)
    print("[assistant] Thinking...")
    response = assistant.answer(question)
    time.sleep(UX_DELAY_SECONDS)
    print("[assistant] Composing answer...")
    time.sleep(UX_DELAY_SECONDS / 2)
    print(f"\nFocus: {response.focus}")
    print("Answer:")
    print(response.answer)
    if show_context:
        print("\nMarkdown context:")
        print(response.context)
    print()
    return response.answer


def _generate_markdown_docs(repo_identifier: str, target_dir: str) -> int:
    path = Path(target_dir)
    path.mkdir(parents=True, exist_ok=True)

    files: dict[str, str] = {
        "01-co-to-robi.md": f"""# Co to robi

Repozytorium `{repo_identifier}` to CLI onboarding assistant, który:
- czyta lokalny kontekst z plików Markdown,
- odpowiada przez Vapi na pytania onboardingowe,
- wspiera tematykę: cel projektu, build/setup, architektura, integracje.

## Dla kogo
- nowi członkowie zespołu,
- osoby wdrażające się w projekt.
""",
        "02-architektura.md": """# Architektura

## Główne komponenty
- `onboarding_cli/cli.py` – wejście CLI (`ask`, `chat`, `generate-md`).
- `onboarding_cli/assistant.py` – orkiestracja: klasyfikacja pytania + odpowiedź.
- `onboarding_cli/markdown_context_client.py` – ładowanie kontekstu z plików `.md`.
- `onboarding_cli/vapi_client.py` – połączenie z Vapi API.
- `onboarding_cli/config.py` – konfiguracja ENV i walidacja.

## Przepływ
1. Użytkownik zadaje pytanie.
2. Kontekst ładowany jest z lokalnych plików Markdown.
3. Prompt z kontekstem trafia do Vapi.
4. CLI zwraca odpowiedź.
""",
        "03-modele-baza.md": """# Modele / baza danych

## Modele
- Model LLM jest po stronie Vapi (konfigurowany po stronie asystenta Vapi).
- Po stronie CLI nie ma lokalnego modelu inferencyjnego.

## Baza danych
- Brak lokalnej bazy danych.
- Źródłem wiedzy onboardingowej są pliki Markdown w `docs/context/`.
""",
        "04-jak-to-postawic.md": """# Jak to postawić

## Wymagania
- Python 3.10+
- konto i klucze Vapi

## Kroki
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `python3 -m pip install -e .`
3. Uzupełnij `.env` (`VAPI_API_KEY`, `VAPI_ASSISTANT_ID`, itd.)
4. Wygeneruj/uzupełnij markdowny:
   - `python3 -m onboarding_cli.cli generate-md`
5. Uruchom:
   - `python3 -m onboarding_cli.cli chat`
""",
        "05-polaczenia-zewnetrzne.md": """# Połączenia zewnętrzne

## Vapi
- Endpoint: `VAPI_BASE_URL + VAPI_CHAT_PATH`
- Auth: `Authorization: Bearer VAPI_API_KEY`
- Wymagany `VAPI_ASSISTANT_ID`.
""",
    }

    for filename, content in files.items():
        (path / filename).write_text(content.strip() + "\n", encoding="utf-8")

    print(f"Generated Markdown docs in: {path}")
    return 0


def _interactive_mode(
    assistant: OnboardingAssistant, show_context: bool, repo_identifier: str
) -> int:
    print("Onboarding assistant started. Ask questions about purpose/build/architecture/integrations.")
    print(f"Repository: {repo_identifier}")
    print("Type 'exit' or 'quit' to stop.\n")
    while True:
        try:
            question = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return 0

        if not question:
            continue
        if question.lower() in {"exit", "quit"}:
            print("Exiting.")
            return 0

        _print_response(assistant, question, show_context)


def _voice_chat_mode(
    assistant: OnboardingAssistant,
    show_context: bool,
    repo_identifier: str,
    config: AppConfig,
) -> int:
    voice = VoiceIO(
        language=config.voice_language,
        tts_rate=config.voice_tts_rate,
        input_device=config.voice_input_device,
        use_pyaudio=config.voice_use_pyaudio,
    )
    print("Onboarding voice chat started.")
    print(f"Repository: {repo_identifier}")
    print("Press Enter to speak. Type 'exit' and Enter to stop.\n")
    while True:
        try:
            signal = input("[voice] Enter=listen, exit=quit > ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            return 0

        if signal in {"exit", "quit"}:
            print("Exiting.")
            return 0

        print("[voice] Listening...")
        question, error = voice.listen_once()
        if error:
            print(f"[voice] {error}")
            continue
        if not question:
            print("[voice] Empty speech input.")
            continue

        print(f"\nYou said: {question}")
        answer = _print_response(assistant, question, show_context)
        print("[voice] Speaking...")
        voice.speak(answer)


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="onboarder",
        description="CLI onboarding assistant backed by Markdown context and Vapi",
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Print raw Markdown context together with the final answer.",
    )

    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a single onboarding question.")
    ask_parser.add_argument("question", help="Question to ask the onboarding assistant.")

    subparsers.add_parser("chat", help="Start interactive onboarding chat.")
    subparsers.add_parser("voice-chat", help="Start voice chat: microphone in, spoken answer out.")
    generate_parser = subparsers.add_parser(
        "generate-md",
        help="Generate onboarding Markdown files used as local context.",
    )
    generate_parser.add_argument(
        "--output-dir",
        default="./docs/context",
        help="Directory for generated Markdown files (default: ./docs/context).",
    )

    args = parser.parse_args()

    if args.command == "generate-md":
        repo_identifier = _resolve_repo_identifier_lightweight()
        return _generate_markdown_docs(repo_identifier, args.output_dir)

    try:
        config = load_config()
        assistant, repo_identifier = _build_assistant(config)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.command == "ask":
        print(f"Repository: {repo_identifier}")
        _print_response(assistant, args.question, args.show_context)
        return 0

    if args.command == "voice-chat":
        return _voice_chat_mode(assistant, args.show_context, repo_identifier, config)

    return _interactive_mode(assistant, args.show_context, repo_identifier)


if __name__ == "__main__":
    raise SystemExit(main())
