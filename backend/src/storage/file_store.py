"""Local file storage implementation."""

from __future__ import annotations

from pathlib import Path


class LocalFileStore:
    def __init__(self, base_path: str | Path = "storage") -> None:
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save(self, path: str, content: bytes) -> str:
        target = self.base_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        return str(target)

    def delete(self, path: str) -> None:
        target = self.base_path / path
        if target.exists():
            target.unlink()

    def url(self, path: str) -> str:
        return f"/static/{path}" if not path.startswith("http") else path


__all__ = ["LocalFileStore"]
