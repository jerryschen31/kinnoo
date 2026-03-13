from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


SQL_INJECTION = "SQL_INJECTION"
SHELL_INJECTION = "SHELL_INJECTION"
PATH_TRAVERSAL = "PATH_TRAVERSAL"
SSRF = "SSRF"
XSS = "XSS"
TEMPLATE_INJECTION = "TEMPLATE_INJECTION"


@dataclass(frozen=True)
class InputWarning:
    threat_category: str
    description: str
    param_name: str | None = None


@dataclass(frozen=True)
class InputGuardResult:
    safe: bool
    warnings: list[InputWarning]


class InputGuard(Protocol):
    def check(self, value: str, input_type: str = "text") -> InputGuardResult:
        ...

    def check_inputs(self, inputs: list[tuple[str, str, str]]) -> InputGuardResult:
        ...


class RegexInputGuard:
    """Placeholder V1 guard. Full regex implementation is added in task117."""

    def check(self, value: str, input_type: str = "text") -> InputGuardResult:
        _ = value, input_type
        return InputGuardResult(safe=True, warnings=[])

    def check_inputs(self, inputs: list[tuple[str, str, str]]) -> InputGuardResult:
        aggregate_warnings: list[InputWarning] = []
        for _param_name, value, input_type in inputs:
            result = self.check(value=value, input_type=input_type)
            aggregate_warnings.extend(result.warnings)
        return InputGuardResult(safe=len(aggregate_warnings) == 0, warnings=aggregate_warnings)


def get_default_guard() -> InputGuard:
    return RegexInputGuard()
