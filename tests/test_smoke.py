from main import main


def test_smoke() -> None:
    assert main() is None
