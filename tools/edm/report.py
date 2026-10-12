"""Violations and how they are printed."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Violation:
    check: str   # e.g. "layers"
    file: str    # repository-relative path of the model file
    obj: str     # entity, attribute or relationship the violation is about
    rule: str    # short rule name, matching config/edm-rules.yaml where possible
    message: str

    def __str__(self) -> str:
        where = f"{self.file}: {self.obj}" if self.obj else self.file
        return f"[{self.check}] {where}: {self.message} (rule: {self.rule})"


def print_report(check: str, violations: list[Violation], models_read: int) -> int:
    """Print violations; return the process exit code."""
    for v in violations:
        print(v)
    status = "FAIL" if violations else "ok"
    print(f"check_{check}: {status} — {len(violations)} violation(s), {models_read} model file(s) read")
    return 1 if violations else 0
