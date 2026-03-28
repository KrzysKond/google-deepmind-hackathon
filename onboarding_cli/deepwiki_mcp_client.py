from __future__ import annotations

import json
import subprocess


class DeepWikiMcpClient:
    def __init__(
        self,
        cli_binary: str,
        config_path: str,
        server_name: str,
        repo_name: str,
        fallback_message: str,
        repo_identifier: str,
    ) -> None:
        self._cli_binary = cli_binary
        self._config_path = config_path
        self._server_name = server_name
        self._repo_name = repo_name
        self._fallback_message = fallback_message
        self._repo_identifier = repo_identifier

    def ask(self, question: str) -> str:
        tool_args = {
            "repoName": self._repo_name,
            "question": f"[Repository: {self._repo_identifier}]\n{question}",
        }
        for command in self._build_commands(tool_args):
            result = self._run(command)
            if result is None:
                continue
            if result.returncode != 0:
                if self._is_cli_syntax_error(result.stderr):
                    continue
                return self._build_process_error(result.stderr)

            parsed = self._parse_output(result.stdout)
            if parsed:
                return parsed
            if self._is_cli_syntax_error(result.stderr):
                continue
            return self._build_process_error(result.stderr) or self._fallback_message

        return (
            "DeepWiki MCP call failed: unsupported CLI command style. "
            "Set DEEPWIKI_MCP_CLI_BIN=remote-mcp-cli or install a compatible MCP CLI."
        )

    def _build_commands(self, tool_args: dict[str, str]) -> list[list[str]]:
        serialized_args = json.dumps(tool_args)
        return [
            [
                self._cli_binary,
                "call",
                "--config",
                self._config_path,
                "--server",
                self._server_name,
                "--tool",
                "ask_question",
                "--input",
                serialized_args,
            ],
            [
                self._cli_binary,
                "call",
                "--config-file",
                self._config_path,
                "--server",
                self._server_name,
                "--tool",
                "ask_question",
                "--input",
                serialized_args,
            ],
            [
                self._cli_binary,
                "call",
                self._server_name,
                "ask_question",
                serialized_args,
                "--configpath",
                self._config_path,
                "--raw",
            ],
        ]

    def _run(self, command: list[str]) -> subprocess.CompletedProcess[str] | None:
        try:
            return subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except Exception:
            return None

    def _parse_output(self, output: str) -> str:
        content = output.strip()
        if not content:
            return ""

        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return content

        if isinstance(payload, dict):
            maybe_error = payload.get("error")
            if isinstance(maybe_error, dict) and maybe_error.get("message"):
                return f"DeepWiki MCP error: {maybe_error['message']}"
            structured = payload.get("structuredContent")
            if isinstance(structured, dict):
                result = structured.get("result")
                if isinstance(result, str) and result.strip():
                    return result.strip()
            content = payload.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        text = item.get("text")
                        if isinstance(text, str) and text.strip():
                            return text.strip()
            if "result" in payload:
                return self._normalize(payload["result"])

        return self._normalize(payload)

    @staticmethod
    def _normalize(data: object) -> str:
        if data is None:
            return ""
        if isinstance(data, str):
            return data.strip()
        return json.dumps(data, indent=2, ensure_ascii=True)

    def _build_process_error(self, stderr: str) -> str:
        detail = " ".join(stderr.strip().split())
        if detail:
            return f"DeepWiki MCP call failed: {detail[:500]}"
        return self._fallback_message

    @staticmethod
    def _is_cli_syntax_error(stderr: str) -> bool:
        return ("No such command" in stderr) or ("No such option" in stderr)
