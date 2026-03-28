from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse


def _load_dotenv(dotenv_path: str = ".env") -> None:
    path = Path(dotenv_path)
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        if key and key not in os.environ:
            os.environ[key] = value


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@dataclass(frozen=True)
class AppConfig:
    vapi_api_key: str
    vapi_base_url: str
    vapi_chat_path: str
    vapi_assistant_id: str
    deepwiki_mcp_config_path: str
    deepwiki_mcp_server: str
    deepwiki_mcp_cli_bin: str
    deepwiki_repo_name: str
    deepwiki_fallback_message: str
    repo_identifier: str
    system_context: str


def _normalize_repo_identifier(value: str) -> str:
    return value.strip().rstrip("/").removesuffix(".git")


def _parse_git_remote(remote_url: str) -> str | None:
    remote_url = remote_url.strip()
    if not remote_url:
        return None

    if "://" in remote_url:
        parsed = urlparse(remote_url)
        if not parsed.hostname:
            return None
        path = parsed.path.strip("/").removesuffix(".git")
        if not path:
            return None
        return f"{parsed.hostname}/{path}"

    # SCP-like git remote: git@github.com:org/repo.git
    match = re.match(r"^[^@]+@([^:]+):(.+)$", remote_url)
    if match:
        host, path = match.groups()
        path = path.strip("/").removesuffix(".git")
        if not path:
            return None
        return f"{host}/{path}"

    return None


def _detect_repo_from_git() -> str | None:
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return None

    if result.returncode != 0:
        return None

    return _parse_git_remote(result.stdout)


def _resolve_repo_identifier() -> str:
    explicit_repo = os.getenv("TARGET_REPO", "").strip()
    if explicit_repo:
        return _normalize_repo_identifier(explicit_repo)

    detected_repo = _detect_repo_from_git()
    if not detected_repo:
        raise ValueError(
            "Unknown repository. Set TARGET_REPO (e.g. github.com/org/repo) "
            "or run this CLI inside a git repository with remote.origin.url."
        )
    return _normalize_repo_identifier(detected_repo)


def _derive_deepwiki_repo_name(repo_identifier: str) -> str:
    explicit_repo_name = os.getenv("DEEPWIKI_REPO_NAME", "").strip()
    if explicit_repo_name:
        return explicit_repo_name

    parts = [segment for segment in repo_identifier.split("/") if segment]
    if len(parts) >= 3:
        # host/owner/repo -> owner/repo
        return "/".join(parts[1:])
    if len(parts) == 2:
        return "/".join(parts)
    return repo_identifier


def _resolve_mcp_config_path() -> str:
    configured = os.getenv("DEEPWIKI_MCP_CONFIG_PATH", "./mcp_servers.json").strip()
    configured_path = Path(configured)
    if configured_path.exists():
        return configured

    if configured == "./mcp_servers.json":
        fallback = Path("./mcp_servers.example.json")
        if fallback.exists():
            return str(fallback)
    return configured


def load_config() -> AppConfig:
    _load_dotenv(".env")
    repo_identifier = _resolve_repo_identifier()

    return AppConfig(
        vapi_api_key=_required("VAPI_API_KEY"),
        vapi_base_url=os.getenv("VAPI_BASE_URL", "https://api.vapi.ai").strip(),
        vapi_chat_path=os.getenv("VAPI_CHAT_PATH", "/chat").strip(),
        vapi_assistant_id=_required("VAPI_ASSISTANT_ID"),
        deepwiki_mcp_config_path=_resolve_mcp_config_path(),
        deepwiki_mcp_server=os.getenv("DEEPWIKI_MCP_SERVER", "deepwiki").strip(),
        deepwiki_mcp_cli_bin=os.getenv("DEEPWIKI_MCP_CLI_BIN", "remote-mcp-cli").strip(),
        deepwiki_repo_name=_derive_deepwiki_repo_name(repo_identifier),
        deepwiki_fallback_message=os.getenv(
            "DEEPWIKI_FALLBACK_MESSAGE",
            (
                "I could not retrieve DeepWiki context. Verify mcp-cli installation and "
                "DeepWiki MCP configuration."
            ),
        ).strip(),
        repo_identifier=repo_identifier,
        system_context=os.getenv(
            "SYSTEM_CONTEXT",
            (
                "You are an onboarding assistant. Focus on project purpose, build "
                "instructions, architecture, and external service integrations."
            ),
        ).strip(),
    )
