# Research: Mailcow Startup Readiness Diagnostics

## System and pain

I operate Mailcow Dockerized locally in Ubuntu 24.04.5 inside Colima.
After restarting the environment, I have repeatedly needed to inspect
containers, networks, DNS, Postfix, Dovecot, MariaDB and Redis manually.

The key problem is that Docker reporting a container as running does
not establish that the application is ready.

## Initial measured baseline

Environment: 18 configured Mailcow Compose services.

Observed:
- 18/18 containers running.
- 2 containers report Docker healthcheck status healthy.
- 16 containers have no Docker healthcheck configured.
- SMTP greeting: PASS.
- IMAP greeting: PASS.
- MariaDB protocol handshake: PASS.
- Redis: reachable, authentication required.

Previously measured command execution:
- docker compose config --services: 0.479 seconds.
- docker compose ps --format json: 1.259 seconds.

These are individual command timings, not a full startup-time measurement.
The application probe timings are recorded in the README and benchmark output.

## Existing approaches evaluated

1. Docker healthchecks:
   Mailcow currently exposes healthy status for some services, including
   Unbound and ClamAV in my installation. This does not provide a complete
   application-level readiness view for all 18 services.

2. Docker Compose dependency ordering:
   Compose dependency ordering can ensure that a dependency is started.
   The service_started condition does not establish application readiness.
   A service_healthy condition requires an applicable healthcheck.

These are existing mechanisms, not claims that a maintainer's previous
patch or PR failed.

## Sources reviewed

1. Mailcow installation documentation:
   https://docs.mailcow.email/getstarted/install/

   - Documents the supported Docker Compose startup workflow.
   - Establishes the operational context for starting Mailcow.
   - Provides the official baseline installation procedure.

2. Docker Compose service reference:
   https://docs.docker.com/reference/compose-file/services/

   - Explains depends_on and dependency ordering.
   - Distinguishes service_started from service_healthy.
   - Explains how healthchecks communicate readiness to Compose.

## Measurement plan

Create a repeatable benchmark that compares the time and coverage of
the existing manual diagnostic workflow with Mailcow Startup Doctor.

Do not interpret a successful TCP greeting as proof of authentication
or successful end-to-end mail delivery.

## Scope

Build a read-only diagnostic CLI. Do not modify Mailcow configuration,
restart containers, access mailbox contents or change database data.
