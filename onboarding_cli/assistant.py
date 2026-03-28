from __future__ import annotations

from dataclasses import dataclass

from onboarding_cli.deepwiki_mcp_client import DeepWikiMcpClient
from onboarding_cli.vapi_client import VapiClient


Focus = str


@dataclass
class AssistantAnswer:
    focus: Focus
    answer: str
    deepwiki_context: str


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
        deepwiki_client: DeepWikiMcpClient,
        vapi_client: VapiClient,
        system_context: str,
    ) -> None:
        self._deepwiki_client = deepwiki_client
        self._vapi_client = vapi_client
        self._system_context = system_context

    def answer(self, question: str) -> AssistantAnswer:
        focus = classify_focus(question)
        deepwiki_context = self._deepwiki_client.ask(question)
        answer = self._vapi_client.generate_answer(
            question=question,
            focus=focus,
            deepwiki_context=deepwiki_context,
            system_context=self._system_context,
        )
        return AssistantAnswer(
            focus=focus,
            answer=answer,
            deepwiki_context=deepwiki_context,
        )
