# Benchmark Results

## Environment

- Mailcow Dockerized
- Ubuntu 24.04.5 inside Colima
- Python 3.12
- Five iterations per workflow

## Results

| Metric | Before: separate commands | After: consolidated CLI |
|---|---:|---:|
| Runs | 5 | 5 |
| Median | 3385.08 ms | 2066.39 ms |
| Minimum | 2285.76 ms | 1588.41 ms |
| Maximum | 5010.20 ms | 4947.76 ms |

Median execution-time reduction: 1318.69 ms (39.0%).

Relative speedup: 1.64x.

## Method

Run:

    PYTHONPATH=src python3 bench/benchmark.py

The before workflow invokes Compose inspection commands and launches
separate Python processes for SMTP, IMAP, MariaDB and Redis probes.

The after workflow invokes the consolidated Mailcow Startup Doctor CLI.

## Interpretation and limitations

The result measures diagnostic execution time, not Mailcow startup time
or total human troubleshooting time.

Both workflows perform the same categories of checks. The consolidated
CLI reduces process-launch overhead and provides one combined report.

Only five iterations were measured. Results may vary with system load,
Docker daemon activity and network conditions.

This benchmark does not establish end-to-end mail delivery readiness.
