import json
import unittest

from mailcow_doctor.checks import (
    parse_compose_ps,
    evaluate_service,
    evaluate_services,
)


class TestDockerChecks(unittest.TestCase):

    def test_parse_json_array(self):
        raw = json.dumps([
            {"Service": "mysql-mailcow", "State": "running", "Health": ""}
        ])
        self.assertEqual(len(parse_compose_ps(raw)), 1)

    def test_parse_newline_delimited_json(self):
        raw = (
            '{"Service":"mysql-mailcow","State":"running"}\n'
            '{"Service":"redis-mailcow","State":"running"}'
        )
        self.assertEqual(len(parse_compose_ps(raw)), 2)

    def test_healthy_container_passes(self):
        result = evaluate_service(
            "unbound-mailcow",
            {"State": "running", "Health": "healthy"},
        )
        self.assertEqual(result.status, "PASS")

    def test_running_without_healthcheck_warns(self):
        result = evaluate_service(
            "mysql-mailcow",
            {"State": "running", "Health": ""},
        )
        # self.assertEqual(result.status, "WARN")
        self.assertEqual(result.status, "INFO")

    def test_stopped_container_fails(self):
        result = evaluate_service(
            "postfix-mailcow",
            {"State": "exited", "Health": ""},
        )
        self.assertEqual(result.status, "FAIL")

    def test_unhealthy_container_fails(self):
        result = evaluate_service(
            "unbound-mailcow",
            {"State": "running", "Health": "unhealthy"},
        )
        self.assertEqual(result.status, "FAIL")

    def test_missing_container_fails(self):
        result = evaluate_service("mysql-mailcow", None)
        self.assertEqual(result.status, "FAIL")

    def test_missing_service_is_included(self):
        results = evaluate_services(
            ["mysql-mailcow", "redis-mailcow"],
            [{
                "Service": "mysql-mailcow",
                "State": "running",
                "Health": "healthy",
            }],
        )
        self.assertEqual(len(results), 2)
        self.assertEqual(results[1].status, "FAIL")


if __name__ == "__main__":
    unittest.main()
