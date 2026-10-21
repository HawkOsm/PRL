from pathlib import Path

import pytest

from golden import Golden, RouterCase
from harness import Router, format_report, load, run, save
from run_goldens import main as run_goldens

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


def test_save_then_load_gives_the_same_report(
    cases: list[RouterCase], tmp_path: Path
) -> None:
    report = run(always("PASSTHROUGH"), cases, name="always-passthrough")

    path = save(report, tmp_path / "runs")

    assert path.parent == tmp_path / "runs"
    assert path.suffix == ".json"
    assert load(path) == report


def test_save_makes_a_safe_file_name(cases: list[RouterCase], tmp_path: Path) -> None:
    report = run(always("PASSTHROUGH"), cases, name="my router/v2")

    path = save(report, tmp_path)

    assert path.parent == tmp_path
    assert "/" not in path.name
    assert " " not in path.name


def test_report_text_shows_summary_and_per_class_scores(
    cases: list[RouterCase],
) -> None:
    report = run(always("PASSTHROUGH"), cases, name="always-passthrough")
    right = sum(case.expected == "PASSTHROUGH" for case in cases)
    required = sum(case.must_pass is True for case in cases)

    lines = format_report(report).splitlines()

    assert lines[0].startswith("router[always-passthrough]:")
    assert f"{right}/{len(cases)} correct" in lines[0]
    assert f"must_pass: {required}/{required} ✓" in lines[0]
    class_line = next(line for line in lines if line.startswith("  PASSTHROUGH"))
    assert class_line.endswith(f"{right}/{right}")
    task_new = sum(case.expected == "TASK_NEW" for case in cases)
    wrong_line = next(line for line in lines if line.startswith("  TASK_NEW"))
    assert wrong_line.endswith(f"0/{task_new}")


def test_report_text_lists_failed_cases(cases: list[RouterCase]) -> None:
    report = run(always("TASK_NEW"), cases, name="always-task-new")
    wrong = sum(case.expected != "TASK_NEW" for case in cases)

    text = format_report(report)

    assert "must_pass: 0/" in text
    assert "✗" in text
    assert f"failed ({wrong}):" in text
    assert "[must_pass]" in text


def test_report_text_shows_the_error_of_a_crashing_router(
    cases: list[RouterCase],
) -> None:
    def crashing(message: str, session_active: bool) -> str:
        raise ValueError("boom")

    text = format_report(run(crashing, cases, name="crashing"))

    assert "ValueError: boom" in text


def test_make_goldens_prints_and_saves_one_report_per_router(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    run_goldens(tmp_path)

    output = capsys.readouterr().out
    assert "router[always-passthrough]" in output
    assert "router[always-task-new]" in output
    assert "router[heuristic]" in output
    assert len(list(tmp_path.glob("*.json"))) == 3


def test_one_failed_must_pass_case_fails_the_verdict(cases: list[RouterCase]) -> None:
    # arrange: a router that is right everywhere except for the message "yes"
    def almost_perfect(message: str, session_active: bool) -> str:
        if message == "yes":
            return "TASK_NEW"  # wrong answer for that case
        return "PASSTHROUGH"  # answers PASSTHROUGH for everything, but gets yes wrong

    # act
    report = run(almost_perfect, cases, name="almost-perfect")

    # assert: how many correct? what is the verdict? how many must_pass passed?
    assert report.must_passed is False
    assert report.correct == sum(case.expected == "PASSTHROUGH" for case in cases) - 1 
