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
| Median | 2910.88 ms | 1653.56 ms |
| Minimum | 2249.90 ms | 1472.47 ms |
| Maximum | 4250.38 ms | 2061.60 ms |

Median execution-time reduction: 1257.32 ms (43.2%).

Relative speedup: 1.76x.

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
