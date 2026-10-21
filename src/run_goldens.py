"""Score the routers against the golden cases and print a report for each."""

from pathlib import Path

from golden import Golden
from harness import Router, format_report, run, save
from router import route

ROOT = Path(__file__).resolve().parent.parent
GOLDEN_FILE = ROOT / "tests" / "golden" / "router_cases.jsonl"
RESULTS_DIR = ROOT / "results" / "router"


def always(answer: str) -> Router:
    """Make a baseline router that ignores the message and always gives one answer."""

    def router(message: str, session_active: bool) -> str:
        return answer

    return router


# Routers scored by `make goldens`: two baselines and the heuristic router.
ROUTERS: dict[str, Router] = {
    "always-passthrough": always("PASSTHROUGH"),
    "always-task-new": always("TASK_NEW"),
    "heuristic": route,
}


def main(results_dir: Path = RESULTS_DIR) -> None:
    golden = Golden()
    golden.load_router_cases_from_json(GOLDEN_FILE)
    for name, router in ROUTERS.items():
        report = run(router, golden.router_cases, name=name)
        path = save(report, results_dir)
        print(format_report(report))
        print(f"  saved: {path}\n")


if __name__ == "__main__":
    main()
