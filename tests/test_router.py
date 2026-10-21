from pathlib import Path

import pytest

from golden import Golden, RouterCase
from harness import run
from router import route


@pytest.fixture
def cases() -> list[RouterCase]:
    golden = Golden()
    golden.load_router_cases_from_json(
        Path(__file__).parent / "golden" / "router_cases.jsonl"
    )
    return golden.router_cases


@pytest.mark.parametrize("session_active", [False, True])
def test_a_message_starting_with_slash_is_a_command(session_active: bool) -> None:
    assert route("/help", session_active) == "META"
    assert route("  /quick fix the bug", session_active) == "META"


def test_a_short_follow_up_in_an_active_session_passes_through() -> None:
    assert route("yes", session_active=True) == "PASSTHROUGH"
    assert route("no, the other file", session_active=True) == "PASSTHROUGH"


def test_unsure_messages_fall_back_to_passthrough() -> None:
    # The rules cannot tell a new task or a question apart; only the LLM tier can.
    assert route("fix the udp packet loss issue", session_active=False) == "PASSTHROUGH"
    assert route("what does grep -r do", session_active=False) == "PASSTHROUGH"


def test_it_never_breaks_a_must_pass_case(cases: list[RouterCase]) -> None:
    report = run(route, cases, name="heuristic")

    assert report.must_passed is True
    assert all(result.error is None for result in report.results)


def test_it_scores_the_passthrough_floor_on_the_goldens(
    cases: list[RouterCase],
) -> None:
    report = run(route, cases, name="heuristic")

    # Only PASSTHROUGH answers, no META in the goldens: the floor is every
    # PASSTHROUGH case. Beating this needs the LLM tier (M4).
    assert report.correct == sum(case.expected == "PASSTHROUGH" for case in cases)
