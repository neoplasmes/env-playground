import os
import unittest
from unittest.mock import patch

import reconcile


class ReconcileTest(unittest.TestCase):
    def test_verification_requires_successful_woodpecker_check(self):
        cases = [
            ([], False),
            ([{"context": "other/check", "state": "success"}], False),
            ([{"context": "ci/woodpecker/push/checks", "state": "pending"}], False),
            ([{"context": "ci/woodpecker/push/checks", "state": "failure"}], False),
            (
                [
                    {"context": "ci/woodpecker/push/checks", "state": "success"},
                    {"context": "ci/woodpecker/cron/delivery", "state": "pending"},
                ],
                True,
            ),
        ]
        for statuses, expected in cases:
            with (
                self.subTest(statuses=statuses),
                patch.object(reconcile, "github", return_value={"statuses": statuses}),
            ):
                self.assertEqual(reconcile.verified("a" * 40), expected)

    def test_closed_preview_removed_and_fork_not_deployed(self):
        responses = [
            [
                {
                    "number": 2,
                    "draft": False,
                    "head": {"sha": "b" * 40, "repo": {"full_name": "fork/repo"}},
                }
            ],
            {"sha": "a" * 40},
        ]
        with (
            patch.dict(os.environ, {"PLAYGROUND_DOMAIN": "1-2-3-4.sslip.io"}),
            patch.object(reconcile, "github", side_effect=responses),
            patch.object(reconcile, "state", side_effect=[{"pr": "1"}, {}, {}]),
            patch.object(reconcile, "verified", return_value=False),
            patch.object(reconcile, "run") as run,
            patch.object(reconcile, "deploy") as deploy,
        ):
            reconcile.main()
            self.assertEqual(run.call_count, 2)
            self.assertIn("uninstall", run.call_args_list[0].args)
            deploy.assert_not_called()

    def test_preview_limit_preserves_existing_assignments(self):
        pulls = [
            {
                "number": number,
                "draft": False,
                "head": {
                    "sha": str(number) * 40,
                    "repo": {"full_name": reconcile.REPOSITORY},
                },
            }
            for number in range(1, 5)
        ]
        with (
            patch.dict(os.environ, {"PLAYGROUND_DOMAIN": "1-2-3-4.sslip.io"}),
            patch.object(reconcile, "github", side_effect=[pulls, {"sha": "a" * 40}]),
            patch.object(
                reconcile, "state", side_effect=[{"pr": "3"}, {"pr": "2"}, {"pr": "1"}]
            ),
            patch.object(reconcile, "verified", return_value=True),
            patch.object(reconcile, "deploy") as deploy,
        ):
            reconcile.main()
            self.assertEqual(deploy.call_count, 4)
            self.assertEqual(deploy.call_args_list[1].args[0], "preview-3")
            self.assertEqual(deploy.call_args_list[3].args[0], "preview-1")

    def test_invalid_sha_never_reaches_shell(self):
        with patch.object(reconcile, "run") as run, self.assertRaises(ValueError):
            reconcile.deploy("dev", "master; echo unsafe", "dev.example.com")
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
