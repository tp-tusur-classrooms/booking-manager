import unittest

from scripts.check_pr import validate_route


class PullRequestPolicyTests(unittest.TestCase):
    def test_working_branches_target_develop(self) -> None:
        for head in ("feature/DEV-01-repository-ci", "fix/BUG-12-login"):
            with self.subTest(head=head):
                validate_route("develop", head, same_repository=True)

    def test_fork_working_branch_can_target_develop(self) -> None:
        validate_route("develop", "feature/DEV-01-ci", same_repository=False)

    def test_only_own_develop_can_target_main(self) -> None:
        validate_route("main", "develop", same_repository=True)
        for head, same_repository in (
            ("feature/DEV-01-ci", True),
            ("develop", False),
            ("master", True),
        ):
            with (
                self.subTest(head=head, same_repository=same_repository),
                self.assertRaises(ValueError),
            ):
                validate_route("main", head, same_repository=same_repository)

    def test_invalid_working_branch_names_fail(self) -> None:
        for head in (
            "main",
            "dev",
            "feature/login",
            "fix/DEV-01-",
            "feature/DEV-01-CI",
        ):
            with self.subTest(head=head), self.assertRaises(ValueError):
                validate_route("develop", head, same_repository=True)

    def test_unknown_base_fails(self) -> None:
        with self.assertRaises(ValueError):
            validate_route("master", "develop", same_repository=True)
