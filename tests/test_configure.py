import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import configure

from src.low.config.reader import ConfigReader
from src.low.creds.reader import CredsReader


class ConfigureTests(unittest.TestCase):
    def test_example_configuration_matches_application_schema(self) -> None:
        ConfigReader.load(Path("config/example/config.json"))
        CredsReader.load(Path("config/example/creds.json"))

    def test_creates_random_secret_and_preserves_existing_configuration(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree("config/example", root / "config/example")
            with patch.object(
                configure, "__file__", str(root / "scripts/configure.py")
            ):
                configure.main()
                creds_path = root / "config/prod/creds.json"
                config_path = root / "config/prod/config.json"
                creds = CredsReader.load(creds_path)
                example = CredsReader.load(root / "config/example/creds.json")
                self.assertNotEqual(
                    creds.modules.token.secret_key, example.modules.token.secret_key
                )
                self.assertGreaterEqual(len(creds.modules.token.secret_key), 48)
                config_data = json.loads(config_path.read_text())
                config_data["settings"]["PROJECT_NAME"] = "Custom local settings"
                config_path.write_text(json.dumps(config_data))
                previous_creds = creds_path.read_bytes()
                previous_config = config_path.read_bytes()
                configure.main()
                self.assertEqual(creds_path.read_bytes(), previous_creds)
                self.assertEqual(config_path.read_bytes(), previous_config)
