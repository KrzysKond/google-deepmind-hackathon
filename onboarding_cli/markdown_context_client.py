from __future__ import annotations

from pathlib import Path


class MarkdownContextClient:
    def __init__(self, context_dir: str, max_chars: int = 12000) -> None:
        self._context_dir = Path(context_dir)
        self._max_chars = max(1000, max_chars)

    def ask(self, question: str) -> str:
        files = self._list_markdown_files()
        if not files:
            return (
                f"Markdown context unavailable: no .md files found in "
                f"{self._context_dir}."
            )

        selected = self._select_relevant_files(question, files)
        chunks: list[str] = []
        total = 0
        for path in selected:
            content = path.read_text(encoding="utf-8", errors="replace").strip()
            if not content:
                continue
            block = f"# Source: {path.name}\n\n{content}\n"
            total += len(block)
            if total > self._max_chars:
                break
            chunks.append(block)

        if not chunks:
            return (
                f"Markdown context unavailable: files exist in {self._context_dir}, "
                "but they are empty."
            )

        return "\n\n".join(chunks)

    def _list_markdown_files(self) -> list[Path]:
        if not self._context_dir.exists():
            return []
        return sorted(
            [path for path in self._context_dir.rglob("*.md") if path.is_file()],
            key=lambda path: path.name,
        )

    def _select_relevant_files(self, question: str, files: list[Path]) -> list[Path]:
        text = question.lower()
        ranking: list[tuple[int, Path]] = []
        for path in files:
            score = 0
            name = path.name.lower()
            if any(term in text for term in ("purpose", "goal", "why", "what does it do")):
                if "purpose" in name:
                    score += 5
            if any(term in text for term in ("architecture", "design", "components")):
                if "architecture" in name:
                    score += 5
            if any(term in text for term in ("model", "database", "db", "data")):
                if "model" in name or "database" in name:
                    score += 5
            if any(term in text for term in ("setup", "run", "build", "deploy", "install")):
                if "setup" in name or "build" in name:
                    score += 5
            if any(term in text for term in ("external", "integration", "api", "connection")):
                if "connection" in name or "integration" in name:
                    score += 5
            ranking.append((score, path))

        ranking.sort(key=lambda item: (item[0], item[1].name), reverse=True)
        top = [path for score, path in ranking if score > 0][:3]
        if top:
            return top + [path for path in files if path not in top]
        return files
