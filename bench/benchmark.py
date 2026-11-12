"""Compare separate manual-style checks with the consolidated CLI."""

import argparse
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMPOSE_DIR_DEFAULT = "/opt/mailcow-dockerized"

PROBES = [
    ("SMTP", "check_smtp"),
    ("IMAP", "check_imap"),
    ("MariaDB", "check_mariadb"),
    ("Redis", "check_redis"),
]


def run(command, cwd=None, env=None):
    return subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=True,
    )


def manual_style_workflow(compose_dir, env):
    """Run the checks as separate commands, as in a manual checklist."""
    run(
        ["docker", "compose", "config", "--services"],
        cwd=compose_dir,
        env=env,
    )
    run(
        ["docker", "compose", "ps", "--format", "json"],
        cwd=compose_dir,
        env=env,
    )

    for name, function_name in PROBES:
        code = (
            f"from mailcow_doctor.protocols import {function_name}; "
            f"r = {function_name}(); "
            f"print(r.status, r.detail); "
            "raise SystemExit(1 if r.status == 'FAIL' else 0)"
        )
        run(
            [sys.executable, "-c", code],
            cwd=ROOT,
            env=env,
        )


def consolidated_workflow(compose_dir, env):
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "mailcow_doctor.cli",
            "--compose-dir",
            compose_dir,
        ],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )

    # Exit code 1 is expected when the installation is DEGRADED.
    if result.returncode not in (0, 1):
        raise RuntimeError(
            f"CLI failed with exit code {result.returncode}: "
            f"{result.stderr}\n{result.stdout}"
        )

    if "Mailcow Startup Doctor" not in result.stdout:
        raise RuntimeError("CLI did not produce its diagnostic report")


def measure(function, runs):
    samples = []

    for _ in range(runs):
        start = time.perf_counter()
        function()
        samples.append((time.perf_counter() - start) * 1000)

    return samples


def report(label, samples):
    print(f"{label}:")
    print(f"  Runs:   {len(samples)}")
    print(f"  Median: {statistics.median(samples):.2f} ms")
    print(f"  Min:    {min(samples):.2f} ms")
    print(f"  Max:    {max(samples):.2f} ms")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--compose-dir",
        default=COMPOSE_DIR_DEFAULT,
    )
    parser.add_argument("--runs", type=int, default=5)
    args = parser.parse_args()

    if args.runs < 3:
        parser.error("--runs must be at least 3")

    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(ROOT / "src") + (os.pathsep + existing if existing else "")
    )

    print("Mailcow diagnostic workflow benchmark")
    print(f"Compose directory: {args.compose_dir}")
    print(f"Iterations: {args.runs}")
    print()

    manual = measure(
        lambda: manual_style_workflow(args.compose_dir, env),
        args.runs,
    )
    consolidated = measure(
        lambda: consolidated_workflow(args.compose_dir, env),
        args.runs,
    )

    report("Before: separate manual-style commands", manual)
    print()
    report("After: consolidated diagnostic CLI", consolidated)

    before = statistics.median(manual)
    after = statistics.median(consolidated)

    print()
    print(f"Median time difference: {before - after:.2f} ms")
    if after < before:
        print(f"Relative speedup: {before / after:.2f}x")
    else:
        print(
            "The consolidated CLI is not faster in this run. "
            "Its benefit is unified reporting and fewer manual steps."
        )


if __name__ == "__main__":
    main()
