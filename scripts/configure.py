"""Create local configuration without replacing existing settings."""

import json
from pathlib import Path
import secrets
import shutil


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    source = root / "config/example"
    target = root / "config/prod"
    target.mkdir(parents=True, exist_ok=True)
    if not (target / "config.json").exists():
        shutil.copyfile(source / "config.json", target / "config.json")
    creds_path = target / "creds.json"
    if not creds_path.exists():
        creds = json.loads((source / "creds.json").read_text())
        creds["modules"]["token"]["secret_key"] = secrets.token_urlsafe(48)
        creds_path.write_text(json.dumps(creds, indent=2) + "\n")
        creds_path.chmod(0o600)


if __name__ == "__main__":
    main()
