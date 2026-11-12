"""Pure functions for interpreting Docker Compose service state."""

import json
from dataclasses import dataclass


@dataclass
class ServiceResult:
    name: str
    state: str
    health: str
    status: str
    reason: str


def parse_compose_ps(raw_output: str) -> list[dict]:
    """Parse Docker Compose JSON output (array or newline-delimited JSON)."""
    raw_output = raw_output.strip()

    if not raw_output:
        return []

    try:
        data = json.loads(raw_output)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    except json.JSONDecodeError:
        pass

    records = []
    for line in raw_output.splitlines():
        line = line.strip()
        if line:
            records.append(json.loads(line))

    return records


def evaluate_service(service_name: str, container: dict | None) -> ServiceResult:
    """Classify one configured Compose service."""
    if container is None:
        return ServiceResult(
            service_name, "missing", "unknown", "FAIL",
            "No container found for this service",
        )

    state = str(container.get("State", "unknown")).lower()
    health = str(container.get("Health", "") or "none").lower()

    if state != "running":
        return ServiceResult(
            service_name, state, health, "FAIL",
            f"Container state is {state}",
        )

    if health == "unhealthy":
        return ServiceResult(
            service_name, state, health, "FAIL",
            "Container healthcheck reports unhealthy",
        )

    if health == "healthy":
        return ServiceResult(
            service_name, state, health, "PASS",
            "Container is running and healthy",
        )

    return ServiceResult(
        service_name, state, health, "INFO",
        "Container is running, but no healthcheck is configured",
    )

def evaluate_services(
    configured_services: list[str],
    containers: list[dict],
) -> list[ServiceResult]:
    """Evaluate all replicas of every configured Compose service."""

    by_service = {}

    for container in containers:
        name = container.get("Service")
        if name:
            by_service.setdefault(name, []).append(container)

    priority = {
        "PASS": 0,
        "INFO": 1,
        "WARN": 2,
        "FAIL": 3,
    }

    results = []

    for name in configured_services:
        replicas = by_service.get(name, [])

        if not replicas:
            results.append(evaluate_service(name, None))
            continue

        replica_results = [
            evaluate_service(name, replica)
            for replica in replicas
        ]

        if len(replica_results) == 1:
            results.append(replica_results[0])
            continue

        worst = max(
            replica_results,
            key=lambda result: priority[result.status],
        )

        states = {result.state for result in replica_results}
        healths = {result.health for result in replica_results}

        results.append(
            ServiceResult(
                name=name,
                state=next(iter(states)) if len(states) == 1 else "multiple",
                health=next(iter(healths)) if len(healths) == 1 else "mixed",
                status=worst.status,
                reason=(
                    f"{len(replicas)} replicas evaluated; "
                    f"{sum(r.status == 'FAIL' for r in replica_results)} "
                    f"failed, "
                    f"{sum(r.status == 'WARN' for r in replica_results)} "
                    f"warnings, "
                    f"{sum(r.status == 'INFO' for r in replica_results)} "
                    f"unverified"
                ),
            )
        )

    return results
