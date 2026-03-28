from __future__ import annotations

from dataclasses import dataclass

from onboarding_cli.vapi_client import VapiClient


Focus = str


@dataclass
class AssistantAnswer:
    focus: Focus
    answer: str
    context: str


def classify_focus(question: str) -> Focus:
    text = question.lower()
    if any(term in text for term in ("what is it for", "purpose", "goal", "why")):
        return "purpose"
    if any(term in text for term in ("build", "run", "install", "setup", "compile")):
        return "build"
    if any(term in text for term in ("architecture", "design", "structure", "flow")):
        return "architecture"
    if any(
        term in text
        for term in ("integration", "external", "api", "service", "database", "queue")
    ):
        return "integrations"
    return "general"


class OnboardingAssistant:
    def __init__(
        self,
        context_client: object,
        vapi_client: VapiClient,
        system_context: str,
    ) -> None:
        self._context_client = context_client
        self._vapi_client = vapi_client
        self._system_context = system_context

    def answer(self, question: str) -> AssistantAnswer:
        focus = classify_focus(question)
        context = self._context_client.ask(question)
        if self._is_context_failure(context):
            return AssistantAnswer(
                focus=focus,
                answer=(
                    "Markdown mode: context is unavailable, so I cannot answer this question "
                    "yet. Generate or fill Markdown onboarding files and retry."
                ),
                context=context,
            )
        answer = self._vapi_client.generate_answer(
            question=question,
            focus=focus,
            deepwiki_context=context,
            system_context=self._system_context,
        )
        return AssistantAnswer(
            focus=focus,
            answer=answer,
            context=context,
        )

    @staticmethod
    def _is_context_failure(context: str) -> bool:
        text = context.lower()
        failure_markers = (
            "markdown context unavailable",
            "no .md files found",
        )
        return any(marker in text for marker in failure_markers)