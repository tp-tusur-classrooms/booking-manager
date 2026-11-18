"""Enforce the working branch -> develop -> main pull request route."""

import json
import os
from pathlib import Path
import re


def validate_route(base: str, head: str, *, same_repository: bool) -> None:
    if base == "main":
        if head != "develop" or not same_repository:
            raise ValueError("PRs to main must come from this repository's develop")
    elif base == "develop":
        if not re.fullmatch(
            r"(?:feature|fix)/[A-Za-z]+-\d+-[a-z0-9]+(?:-[a-z0-9]+)*", head
        ):
            raise ValueError("Use feature/<task-id>-<name> or fix/<task-id>-<name>")
    else:
        raise ValueError(f"Unsupported PR base: {base}")


def main() -> None:
    event = json.loads(
        Path(os.environ["GITHUB_EVENT_PATH"]).read_text(encoding="utf-8")
    )
    pr = event["pull_request"]
    validate_route(
        pr["base"]["ref"],
        pr["head"]["ref"],
        same_repository=(pr["head"].get("repo") or {}).get("full_name")
        == pr["base"]["repo"]["full_name"],
    )


if __name__ == "__main__":
    main()
