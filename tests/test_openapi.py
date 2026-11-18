from collections.abc import Iterator
from pathlib import Path
from typing import Any
import unittest

from jsonschema import Draft202012Validator
from openapi_spec_validator import validate
from openapi_spec_validator.readers import read_from_filename

SPEC_PATH = Path(__file__).resolve().parents[1] / "docs" / "openapi.yaml"
METHODS = {"get", "post", "put", "patch", "delete"}


def resolve(spec: dict[str, Any], node: Any) -> Any:
    if isinstance(node, dict):
        if "$ref" in node:
            target: Any = spec
            for part in node["$ref"].removeprefix("#/").split("/"):
                target = target[part]
            return resolve(spec, target)
        return {key: resolve(spec, value) for key, value in node.items()}
    if isinstance(node, list):
        return [resolve(spec, item) for item in node]
    return node


def operations(spec: dict[str, Any]) -> Iterator[tuple[str, dict[str, Any]]]:
    for path, item in spec["paths"].items():
        for method, operation in item.items():
            if method in METHODS:
                yield f"{method.upper()} {path}", operation


def media_examples(operation: dict[str, Any]) -> Iterator[tuple[str, Any, Any]]:
    bodies = [("request", operation.get("requestBody", {}))]
    bodies += list(operation["responses"].items())
    for name, body in bodies:
        for media in body.get("content", {}).values():
            schema = media.get("schema")
            if schema is None:
                continue
            if "example" in media:
                yield name, schema, media["example"]
            for key, example in media.get("examples", {}).items():
                yield f"{name} {key}", schema, example["value"]


class OpenApiContractTests(unittest.TestCase):
    spec: dict[str, Any]

    @classmethod
    def setUpClass(cls) -> None:
        raw, _ = read_from_filename(str(SPEC_PATH))
        cls.spec = dict(raw)

    def test_contract_is_valid_openapi(self) -> None:
        validate(self.spec)

    def test_examples_match_schemas(self) -> None:
        spec = resolve(self.spec, self.spec)
        checked = 0
        for name, operation in operations(spec):
            for example, schema, value in media_examples(operation):
                checked += 1
                with self.subTest(operation=name, example=example):
                    validator = Draft202012Validator(
                        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
                    )
                    errors = [error.message for error in validator.iter_errors(value)]
                    self.assertEqual(errors, [])
        self.assertGreater(checked, 0)

    def test_every_operation_has_success_response(self) -> None:
        for name, operation in operations(self.spec):
            with self.subTest(operation=name):
                self.assertTrue(
                    any(status.startswith("2") for status in operation["responses"])
                )

    def test_protected_operations_describe_unauthorized(self) -> None:
        for name, operation in operations(self.spec):
            if operation.get("security", self.spec["security"]) == []:
                continue
            with self.subTest(operation=name):
                self.assertIn("401", operation["responses"])
