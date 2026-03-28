from __future__ import annotations

import argparse
import sys

from onboarding_cli.assistant import OnboardingAssistant
from onboarding_cli.config import load_config
from onboarding_cli.deepwiki_mcp_client import DeepWikiMcpClient
from onboarding_cli.vapi_client import VapiClient


def _build_assistant() -> tuple[OnboardingAssistant, str]:
    config = load_config()
    deepwiki_client = DeepWikiMcpClient(
        cli_binary=config.deepwiki_mcp_cli_bin,
        config_path=config.deepwiki_mcp_config_path,
        server_name=config.deepwiki_mcp_server,
        repo_name=config.deepwiki_repo_name,
        fallback_message=config.deepwiki_fallback_message,
        repo_identifier=config.repo_identifier,
    )
    vapi_client = VapiClient(
        api_key=config.vapi_api_key,
        base_url=config.vapi_base_url,
        chat_path=config.vapi_chat_path,
        assistant_id=config.vapi_assistant_id,
    )
    assistant = OnboardingAssistant(
        deepwiki_client=deepwiki_client, vapi_client=vapi_client, system_context=config.system_context
    )
    return assistant, config.repo_identifier


def _print_response(assistant: OnboardingAssistant, question: str, show_context: bool) -> None:
    response = assistant.answer(question)
    print(f"\nFocus: {response.focus}")
    print("Answer:")
    print(response.answer)
    if show_context:
        print("\nDeepWiki context:")
        print(response.deepwiki_context)
    print()


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


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="onboarder",
        description="CLI onboarding assistant backed by DeepWiki MCP and Vapi",
    )
    parser.add_argument(
        "--show-context",
        action="store_true",
        help="Print raw DeepWiki context together with the final answer.",
    )

    subparsers = parser.add_subparsers(dest="command")

    ask_parser = subparsers.add_parser("ask", help="Ask a single onboarding question.")
    ask_parser.add_argument("question", help="Question to ask the onboarding assistant.")

    subparsers.add_parser("chat", help="Start interactive onboarding chat.")

    args = parser.parse_args()

    try:
        assistant, repo_identifier = _build_assistant()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.command == "ask":
        print(f"Repository: {repo_identifier}")
        _print_response(assistant, args.question, args.show_context)
        return 0

    return _interactive_mode(assistant, args.show_context, repo_identifier)


if __name__ == "__main__":
    raise SystemExit(main())
