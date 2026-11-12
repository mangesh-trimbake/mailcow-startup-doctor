# Mailcow Startup Doctor

A lightweight Python diagnostic CLI that inspects Docker Compose container
state and performs application-level protocol readiness checks for a
Mailcow installation.

## Problem

A Docker container being in the `running` state does not necessarily mean
the application inside it is ready to serve requests.

Similarly, containers without configured Docker healthchecks cannot provide
a meaningful health status through Docker Compose.

Mailcow Startup Doctor addresses this observability gap by combining:

1. Docker Compose service-state inspection.
2. SMTP and IMAP protocol greeting checks.
3. MariaDB protocol handshake validation.
4. Redis PING response validation.

## Architecture

```text
             Mailcow Startup Doctor
                       |
             +---------+---------+
             |                   |
       Docker Compose       Protocol Probes
             |                   |
       Compose config       +----+----+---------+
       Compose ps           |    |    |         |
                            SMTP IMAP MariaDB  Redis
             |                   |    |    |         |
             +---------+---------+----+----+---------+
                       |
                 Result Classification
                       |
                PASS / INFO / WARN / FAIL
                       |
                  CLI Summary
```

## Requirements

- Python 3.10+
- Docker Engine
- Docker Compose plugin
- A running Mailcow installation

## Run

Clone the repository:

```bash
git clone https://github.com/mangesh-trimbake/mailcow-startup-doctor.git
cd mailcow-startup-doctor
```

Run the diagnostic:

```bash
PYTHONPATH=src python3 -m mailcow_doctor.cli
```

For a custom Mailcow installation directory:

```bash
PYTHONPATH=src python3 -m mailcow_doctor.cli \
  --compose-dir /path/to/mailcow-dockerized
```

Run tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Checks performed

| Component | Check | What it verifies |
|---|---|---|
| Docker Compose | Service inventory | Configured services and container presence |
| Docker Compose | Container state | Running, stopped or missing containers |
| Docker Compose | Health status | Existing Docker healthcheck result |
| Postfix | SMTP greeting | TCP connection and SMTP 220 greeting |
| Dovecot | IMAP greeting | TCP connection and IMAP `* OK` greeting |
| MariaDB | MySQL handshake | Initial MySQL/MariaDB protocol handshake |
| Redis | PING | Redis PING response or authentication requirement |

## Result classifications

| Status | Meaning |
|---|---|
| PASS | Check succeeded |
| INFO | Container is running without a configured Docker healthcheck |
| WARN | Service is reachable but requires additional verification |
| FAIL | A check detected a failure |

Overall status:

- HEALTHY: No warnings or failures.
- DEGRADED: At least one warning, but no failures.
- FAIL: At least one failure.

## Local test results

Tested against a local Mailcow installation running in an Ubuntu
24.04.5 environment inside Colima.

Observed results:

- 18 configured Compose services.
- 18 containers running.
- 2 Docker healthchecks reporting healthy.
- 16 containers without Docker healthchecks.
- SMTP greeting check passed.
- IMAP greeting check passed.
- MariaDB protocol handshake passed.
- Redis reachable; authentication required.
- 23 automated tests passed.

The measured protocol probe latencies during one run were:

| Probe | Latency |
|---|---:|
| SMTP | 518.20 ms |
| IMAP | 17.58 ms |
| MariaDB | 21.34 ms |
| Redis | 7.92 ms |

These are observations from one local run, not performance guarantees.

## Design decisions

- Uses Docker Compose rather than relying on hardcoded container names.
- Includes configured services even when their containers are missing.
- Separates container state from application-level readiness.
- Uses protocol-level checks instead of treating an open TCP port as sufficient.
- Uses bounded connection and subprocess timeouts.
- Keeps protocol checks independent and testable.
- Does not modify the Mailcow installation or its configuration.

## Limitations

- MariaDB validation checks the initial protocol handshake, not an
  authenticated SQL query.
- Redis validation detects authentication requirements but does not
  authenticate using Mailcow credentials.
- SMTP and IMAP checks validate initial greetings, not mailbox login,
  message submission or end-to-end delivery.
- Not every Mailcow service has an application-specific probe.
- A successful probe does not guarantee that the entire email system
  is operational.
- Default probe ports assume the standard local Mailcow port mappings.

## Safety

This tool is diagnostic only. It does not restart containers, change
Mailcow configuration, modify databases or send email.

Do not commit Mailcow credentials, environment files, private keys,
certificates or mailbox data.

## Future improvements

- Authenticated MariaDB and Redis checks.
- SMTP submission and authenticated IMAP tests.
- End-to-end test email delivery.
- Configurable probe endpoints.
- Startup dependency and readiness timing analysis.
- Machine-readable JSON output.

## Diagnostic workflow benchmark

A repeatable benchmark compares separate manual-style diagnostic commands
with the consolidated CLI:

```bash
PYTHONPATH=src python3 bench/benchmark.py --runs 5
```


## Latest benchmark

| Metric | Before | After |
|---|---:|---:|
| Median | 2910.88 ms | 1653.56 ms |
| Minimum | 2249.90 ms | 1472.47 ms |
| Maximum | 4250.38 ms | 2061.60 ms |

Median reduction: 43.2%. Relative speedup: 1.76x.

See [benchmark results](bench/RESULTS.md) for methodology and limitations.

## Installation and execution

Run the diagnostic tool: `PYTHONPATH=src python3 -m mailcow_doctor.cli`

Run tests: `PYTHONPATH=src python3 -m pytest -v`

Run benchmark: `PYTHONPATH=src python3 bench/benchmark.py`

## Rollback

The tool is read-only. It does not modify Mailcow containers, configuration, databases or volumes. To remove it, run `rm -rf ~/mailcow-startup-doctor`. No Mailcow rollback is necessary.

## Demonstration

Recording: [Add your five-minute recording URL here]

## Project status

Experimental diagnostic tool. It does not provide complete production-readiness or end-to-end mail delivery verification.
