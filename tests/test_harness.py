from pathlib import Path

import pytest

from golden import Golden, RouterCase
from harness import Router, run

GOLDEN_FILE = Path(__file__).parent / "golden" / "router_cases.jsonl"


@pytest.fixture
def cases() -> list[RouterCase]:
    golden = Golden()
    golden.load_router_cases_from_json(GOLDEN_FILE)
    return golden.router_cases


def always(answer: str) -> Router:
    """Make a fake router that ignores the message and always gives one answer."""

    def router(message: str, session_active: bool) -> str:
        return answer

    return router


def test_always_passthrough(cases: list[RouterCase]) -> None:
    report = run(always("PASSTHROUGH"), cases, name="always-passthrough")

    expected_correct = sum(case.expected == "PASSTHROUGH" for case in cases)
    assert report.router_name == "always-passthrough"
    assert report.total == len(cases)
    assert report.correct == expected_correct
    assert report.accuracy == expected_correct / len(cases)
    assert report.must_passed is True
    assert all(result.got == "PASSTHROUGH" for result in report.results)
    assert all(result.error is None for result in report.results)
    assert all(result.latency_ms >= 0 for result in report.results)


def test_always_task_new_fails_the_must_pass_cases(cases: list[RouterCase]) -> None:
    report = run(always("TASK_NEW"), cases, name="always-task-new")

    assert report.correct == sum(case.expected == "TASK_NEW" for case in cases)
    assert report.must_passed is False


def test_perfect_router_scores_everything(cases: list[RouterCase]) -> None:
    answers = {(case.message, case.session_active): case.expected for case in cases}

    def perfect(message: str, session_active: bool) -> str:
        return answers[(message, session_active)]

    report = run(perfect, cases, name="perfect")

    assert report.correct == report.total == len(cases)
    assert report.must_passed is True


def test_crashing_router_does_not_stop_the_run(cases: list[RouterCase]) -> None:
    def crashing(message: str, session_active: bool) -> str:
        raise ValueError("boom")

    report = run(crashing, cases, name="crashing")

    assert report.total == len(cases)
    assert report.correct == 0
    assert all(result.got is None for result in report.results)
    assert all("boom" in (result.error or "") for result in report.results)


def test_answers_are_compared_ignoring_case(cases: list[RouterCase]) -> None:
    report = run(always("passthrough"), cases, name="lowercase")

    assert report.correct == sum(case.expected == "PASSTHROUGH" for case in cases)


def test_unknown_answer_is_wrong_but_not_an_error(cases: list[RouterCase]) -> None:
    report = run(always("banana"), cases, name="banana")

    assert report.correct == 0
    assert all(result.error is None for result in report.results)


def test_run_does_not_modify_the_cases(cases: list[RouterCase]) -> None:
    before = [case.model_dump() for case in cases]

    run(always("PASSTHROUGH"), cases, name="check")

    assert [case.model_dump() for case in cases] == before
