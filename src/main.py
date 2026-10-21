import argparse


def main() -> None:
    argument = "Hello from prl!"
    argparser = argparse.ArgumentParser(description="Prompt Refine Loop")
    argparser.add_argument(
        "--version",
        action="version",
        version="prl 0.1.0",
    )
    print(argument)


if __name__ == "__main__":
    main()
