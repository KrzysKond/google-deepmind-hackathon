from __future__ import annotations

import json
from urllib import request, error


class VapiClient:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        chat_path: str,
        assistant_id: str,
        max_deepwiki_chars: int = 4000,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._chat_path = chat_path if chat_path.startswith("/") else f"/{chat_path}"
        self._assistant_id = assistant_id
        self._max_deepwiki_chars = max(500, max_deepwiki_chars)

    def generate_answer(
        self,
        question: str,
        focus: str,
        deepwiki_context: str,
        system_context: str,
    ) -> str:
        deepwiki_context = self._trim_context(deepwiki_context)
        prompt = (
            f"{system_context}\n\n"
            f"Focus area: {focus}\n"
            "Use DeepWiki context first. If context is missing, be explicit about "
            "uncertainty and propose next checks.\n\n"
            f"DeepWiki context:\n{deepwiki_context}\n\n"
            f"User question:\n{question}"
        )
        payload = {
            "assistantId": self._assistant_id,
            "input": prompt,
        }
        body = json.dumps(payload).encode("utf-8")
        url = f"{self._base_url}{self._chat_path}"

        http_request = request.Request(
            url=url,
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "curl/8.5.0",
            },
        )

        try:
            with request.urlopen(http_request, timeout=45) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            return f"Vapi HTTP error {exc.code}: {detail}"
        except Exception as exc:
            return f"Vapi request failed: {exc}"

        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            return raw.strip()

        return self._extract_text(parsed)

    @staticmethod
    def _extract_text(payload: object) -> str:
        if isinstance(payload, dict):
            for key in ("output", "text", "message", "response"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()

            messages = payload.get("messages")
            if isinstance(messages, list):
                for item in reversed(messages):
                    if isinstance(item, dict):
                        for key in ("content", "text", "message"):
                            value = item.get(key)
                            if isinstance(value, str) and value.strip():
                                return value.strip()

            return json.dumps(payload, indent=2, ensure_ascii=True)

        if isinstance(payload, str):
            return payload.strip()

        return json.dumps(payload, indent=2, ensure_ascii=True)

    def _trim_context(self, deepwiki_context: str) -> str:
        text = deepwiki_context.strip()
        if len(text) <= self._max_deepwiki_chars:
            return text
        keep = self._max_deepwiki_chars
        return (
            f"{text[:keep]}\n\n"
            "[DeepWiki context truncated to reduce payload size for API compatibility.]"
        )
