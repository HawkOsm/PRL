from collections.abc import Callable
from datetime import UTC, datetime
from time import perf_counter
from typing import Literal

from pydantic import BaseModel

from golden import RouterCase

# A router is any function: (message, session_active) -> class name.
Router = Callable[[str, bool], str]


class CaseResult(BaseModel):
    id: int
    message: str
    session_active: bool
    expected: Literal["TASK_NEW", "PASSTHROUGH", "TRIVIAL"]
    got: str | None = None  # None when the router crashed
    correct: bool
    must_pass: bool = False
    latency_ms: float = 0.0
    error: str | None = None


class Report(BaseModel):
    router_name: str
    run_at: datetime
    results: list[CaseResult]

    @property
    def total(self) -> int:
        """Return the number of cases in the report."""
        return len(self.results)

    @property
    def correct(self) -> int:
        """Return the number of cases classified correctly."""
        return sum(result.correct for result in self.results)

    @property
    def accuracy(self) -> float:
        """Return accuracy as a value between zero and one."""
        return self.correct / self.total if self.total else 0.0

    @property
    def must_passed(self) -> bool:
        """Return whether every required case passed."""
        return all(result.correct for result in self.results if result.must_pass)

    def summary(self) -> dict[str, object]:
        """Return a compact, serialization-friendly report summary."""
        return {
            "router_name": self.router_name,
            "total": self.total,
            "correct": self.correct,
            "accuracy": self.accuracy,
            "must_passed": self.must_passed,
        }


def run_case(router: Router, case: RouterCase) -> CaseResult:
    """Ask the router about one golden case and record what happened."""
    got: str | None = None
    error: str | None = None
    started = perf_counter()
    try:
        got = router(case.message, case.session_active).upper()
    except Exception as exc:  # a crashing router must not stop the whole run
        error = f"{type(exc).__name__}: {exc}"
    latency_ms = (perf_counter() - started) * 1000
    return CaseResult(
        id=case.id,
        message=case.message,
        session_active=case.session_active,
        expected=case.expected,
        got=got,
        correct=got == case.expected,
        must_pass=case.must_pass is True,
        latency_ms=latency_ms,
        error=error,
    )


def run(router: Router, cases: list[RouterCase], name: str) -> Report:
    """Score a router against golden cases. The cases are not modified."""
    return Report(
        router_name=name,
        run_at=datetime.now(UTC),
        results=[run_case(router, case) for case in cases],
    )
