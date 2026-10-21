import re
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Literal

from pydantic import BaseModel

from golden import RouterCase

# A router is any function: (message, session_active) -> class name.
Router = Callable[[str, bool], str]

CLASSES = ("PASSTHROUGH", "TASK_NEW", "TRIVIAL")


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

    @property
    def failures(self) -> list[CaseResult]:
        """Return the cases the router got wrong."""
        return [result for result in self.results if not result.correct]

    def by_class(self) -> dict[str, tuple[int, int]]:
        """Map each expected class to (correct, total)."""
        totals = Counter(result.expected for result in self.results)
        rights = Counter(result.expected for result in self.results if result.correct)
        return {name: (rights[name], totals[name]) for name in CLASSES}

    def must_pass_counts(self) -> tuple[int, int]:
        """Return (must_pass cases passed, must_pass cases in total)."""
        required = [result for result in self.results if result.must_pass]
        return sum(result.correct for result in required), len(required)

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


def save(report: Report, folder: Path) -> Path:
    """Write the report as one JSON file in `folder` and return its path."""
    folder.mkdir(parents=True, exist_ok=True)
    stamp = report.run_at.strftime("%Y%m%dT%H%M%S")
    safe_name = re.sub(r"[^A-Za-z0-9_.-]", "-", report.router_name)
    path = folder / f"{stamp}_{safe_name}.json"
    path.write_text(report.model_dump_json(indent=2))
    return path


def load(path: Path) -> Report:
    """Read a report written by `save`."""
    return Report.model_validate_json(Path(path).read_text())


def describe_failure(result: CaseResult) -> str:
    """One line about a wrong answer: id, expected, what happened, the message."""
    detail = result.error or f"got {result.got}"
    message = result.message
    if len(message) > 50:
        message = message[:47] + "..."
    required = " [must_pass]" if result.must_pass else ""
    return f"  #{result.id} expected {result.expected}, {detail}{required}: {message}"


def format_report(report: Report) -> str:
    """Return the text report: summary, per-class scores, and the failed cases."""
    passed, required = report.must_pass_counts()
    verdict = "✓" if report.must_passed else "✗"
    lines = [
        f"router[{report.router_name}]: {report.correct}/{report.total} correct "
        f"({report.accuracy:.1%}) · must_pass: {passed}/{required} {verdict}"
    ]
    for name, (right, total) in report.by_class().items():
        lines.append(f"  {name:<12} {right}/{total}")
    failures = report.failures
    if failures:
        lines.append(f"failed ({len(failures)}):")
        lines.extend(describe_failure(result) for result in failures)
    return "\n".join(lines)
