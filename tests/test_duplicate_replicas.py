import unittest

from mailcow_doctor.checks import evaluate_services


class TestDuplicateReplicas(unittest.TestCase):

    def test_failed_replica_is_never_hidden(self):
        failed = {
            "Service": "redis-mailcow",
            "State": "exited",
            "Health": "",
        }
        healthy = {
            "Service": "redis-mailcow",
            "State": "running",
            "Health": "healthy",
        }

        for containers in ([failed, healthy], [healthy, failed]):
            with self.subTest(containers=containers):
                results = evaluate_services(
                    ["redis-mailcow"],
                    containers,
                )
                self.assertEqual(results[0].status, "FAIL")

    def test_all_healthy_replicas_pass(self):
        containers = [
            {
                "Service": "redis-mailcow",
                "State": "running",
                "Health": "healthy",
            },
            {
                "Service": "redis-mailcow",
                "State": "running",
                "Health": "healthy",
            },
        ]

        results = evaluate_services(["redis-mailcow"], containers)
        self.assertEqual(results[0].status, "PASS")


if __name__ == "__main__":
    unittest.main()
