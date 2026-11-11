# Design: Mailcow Startup Doctor

## 1. Problem

Docker Compose container state alone does not establish application
readiness.

In my local Mailcow installation:
- 18 configured services were running.
- Only 2 reported healthy Docker healthcheck status.
- 16 had no Docker healthcheck configured.
- SMTP, IMAP and MariaDB protocol checks passed.
- Redis was reachable but required authentication.

The tool combines Docker inspection with application protocol checks.

## 2. Public community evidence

Type: Public GitHub issue report (not a direct interview).

Person: peterschwps
Where: GitHub, mailcow/mailcow-dockerized issue #7582
Date: October 30, 2026

Link:
https://github.com/mailcow/mailcow-dockerized/issues/7582

Three concrete observations reported:

1. Ofelia started while Dovecot was unavailable and did not register
   Dovecot scheduled jobs even after Dovecot became available.

2. Other scheduled jobs continued running, making the missing Dovecot
   jobs less obvious during normal operation.

3. The missing log-trimming job allowed Redis log lists to grow.
   The report recorded approximately 2.6 GB of memory usage and an
   eventual Redis out-of-memory kill.

What changed in my plan:

This report reinforced that checking container state and basic
protocol availability cannot establish that every dependent background
function is working. I therefore kept the tool's results narrowly
scoped and documented that it does not verify Ofelia job registration
or end-to-end Mailcow functionality.

This issue is community evidence, not proof that my local installation
has the same Ofelia failure.

## 3. Architecture

### Docker inspection
- Read configured services using docker compose config.
- Read container states using docker compose ps.
- Identify missing, stopped, healthy and unhealthchecked containers.

### Application probes
- SMTP: validate Postfix 220 greeting.
- IMAP: validate Dovecot * OK greeting.
- MariaDB: validate initial MySQL protocol handshake.
- Redis: issue PING and classify PONG and NOAUTH responses.

### Reporting
- PASS: check succeeded.
- INFO: running without a configured Docker healthcheck.
- WARN: reachable but additional verification is needed.
- FAIL: check detected a failure.

## 4. Engineering trade-offs

### Trade-off 1: Protocol checks versus TCP checks

Chosen: Validate initial application protocol responses.

Rejected: Only checking whether TCP ports accept connections.

Reason: An open port does not establish that the expected application
protocol is responding. Protocol greetings provide stronger evidence.

Cost: These checks do not prove authentication or end-to-end mail delivery.

### Trade-off 2: Read-only diagnostics versus automatic remediation

Chosen: Read-only inspection.

Rejected: Automatically restart containers or rewrite configuration.

Reason: Automatic remediation can hide the original failure or introduce
additional failures. Operators should see diagnostic evidence first.

Cost: Remediation remains a manual operation.

### Trade-off 3: No credentials versus authenticated dependency checks

Chosen: Inspect MariaDB handshake and Redis authentication response
without reading Mailcow secrets.

Rejected: Load credentials and perform authenticated dependency checks.

Reason: Avoid unnecessary secret handling in the initial implementation.

Cost: A MariaDB handshake does not prove SQL query readiness. Redis
NOAUTH does not prove authenticated Redis operations work.

## 5. Deliberately not built

- Automatic container restarts.
- Mailbox login or mailbox data inspection.
- End-to-end email sending and receiving.
- Automatic changes to Mailcow configuration.
- Authenticated database checks.
- Background monitoring daemon or dashboard.
- Ofelia scheduled-job registration verification.

These features increase scope or operational risk and are outside
the initial diagnostic implementation.

## 6. Benchmark

Five-run local benchmark:

- Separate diagnostic commands: 2559.41 ms median.
- Consolidated CLI: 1742.78 ms median.
- Reduction: 816.63 ms (31.9%).
- Relative speedup: 1.47x.

This measures diagnostic execution time, not Mailcow startup time.
