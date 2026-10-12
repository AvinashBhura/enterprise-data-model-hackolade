"""Load config/edm-rules.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

RULES_PATH = Path("config") / "edm-rules.yaml"


@dataclass
class Rules:
    raw: dict

    @classmethod
    def load(cls, repo: Path, path: Path | None = None) -> "Rules":
        p = path or (repo / RULES_PATH)
        with open(p, encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh) or {})

    def section(self, name: str) -> dict:
        return self.raw.get(name) or {}

    @property
    def scope_roots(self) -> list[str]:
        return self.section("scope").get("roots", ["src"])

    @property
    def model_glob(self) -> str:
        return self.section("scope").get("model_glob", "**/*.hck.json")

    @property
    def layers(self) -> list[dict]:
        return self.raw.get("layers") or []

    def layer_for(self, rel_path: str) -> tuple[str | None, int | None]:
        """The layer whose path is the longest prefix of rel_path."""
        best = None
        for layer in self.layers:
            prefix = layer["path"].rstrip("/") + "/"
            if rel_path.startswith(prefix) and (best is None or len(prefix) > len(best[0])):
                best = (prefix, layer["name"], layer["rank"])
        return (best[1], best[2]) if best else (None, None)

    def rank_of(self, layer_name: str) -> int | None:
        for layer in self.layers:
            if layer["name"] == layer_name:
                return layer["rank"]
        return None
