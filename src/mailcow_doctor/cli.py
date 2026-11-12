
"""Command-line interface for Mailcow Startup Doctor."""

import argparse
import subprocess
import sys

from mailcow_doctor.checks import parse_compose_ps, evaluate_services
from mailcow_doctor.protocols import (
    check_smtp,
    check_imap,
    check_mariadb,
    check_redis,
)


def run_command(command: list[str], cwd: str) -> str:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )
    return result.stdout


def print_summary(results):
    counts = {
        status: sum(result.status == status for result in results)
        for status in ("PASS", "INFO", "WARN", "FAIL")
    }
    print(
        f"PASS: {counts['PASS']}  "
        f"INFO: {counts['INFO']}  "
        f"WARN: {counts['WARN']}  "
        f"FAIL: {counts['FAIL']}"
    )
    return counts



def main():
    parser = argparse.ArgumentParser(
        description="Inspect Mailcow Docker Compose and application readiness."
    )
    parser.add_argument(
        "--compose-dir",
        default="/opt/mailcow-dockerized",
        help="Path to the Mailcow Docker Compose directory",
    )
    args = parser.parse_args()

    try:
        services_output = run_command(
            ["docker", "compose", "config", "--services"],
            args.compose_dir,
        )
        configured_services = [
            line.strip()
            for line in services_output.splitlines()
            if line.strip()
        ]

        ps_output = run_command(
            ["docker", "compose", "ps", "--format", "json"],
            args.compose_dir,
        )
        containers = parse_compose_ps(ps_output)
        service_results = evaluate_services(configured_services, containers)

    except subprocess.TimeoutExpired as exc:
        print(f"ERROR: Docker command timed out after {exc.timeout} seconds")
        sys.exit(2)
    except subprocess.CalledProcessError as exc:
        print(f"ERROR: Docker inspection failed: {exc}")
        if exc.stderr:
            print(exc.stderr)
        sys.exit(2)
    except (OSError, ValueError) as exc:
        print(f"ERROR: Could not inspect Compose state: {exc}")
        sys.exit(2)

    protocol_results = [
        check_smtp(),
        check_imap(),
        check_mariadb(),
        check_redis(),
    ]

    print("\nMailcow Startup Doctor")
    print("=" * 70)

    print("\n1. Docker Compose services")
    print("-" * 70)
    for result in service_results:
        print(
            f"[{result.status:4}] {result.name:25} "
            f"state={result.state:10} health={result.health:10} "
            f"{result.reason}"
        )

    print("\n2. Application protocol probes")
    print("-" * 70)
    for result in protocol_results:
        print(
            f"[{result.status:4}] {result.name:20} "
            f"{result.detail} ({result.elapsed_ms:.2f} ms)"
        )

    print("\n3. Summary")
    print("-" * 70)
    service_counts = print_summary(service_results)
    print("Docker services")

    protocol_counts = print_summary(protocol_results)
    print("Application probes")

    all_results = service_results + protocol_results

    if any(result.status == "FAIL" for result in all_results):
        print("\nOverall: FAIL")
        sys.exit(1)

    if any(result.status == "WARN" for result in all_results):
        print("\nOverall: DEGRADED")
        sys.exit(1)

    print("\nOverall: HEALTHY")
    sys.exit(0)


if __name__ == "__main__":
    main()
