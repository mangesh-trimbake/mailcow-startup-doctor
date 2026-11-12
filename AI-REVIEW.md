# AI Code Review: Defects Found in AI-Generated Code

During implementation, I tested AI-generated code against edge cases
that were not covered by the initial happy-path tests.

Three behavioral defects were reproduced, fixed and covered by
regression tests.

## Defect 1: Assuming TCP responses arrive in one read

**Fix commit:** `75b07b4`

**Affected code:** `src/mailcow_doctor/protocols.py`

### Original behavior

The SMTP, IMAP and Redis probes used a single socket `recv()` call
and assumed that it returned the complete protocol response.

TCP is a byte stream. A response can arrive in multiple chunks.
A valid response could therefore be incorrectly classified as a failure.

### Reproduction

Added `tests/test_fragmented_protocols.py`.

The tests simulated:
- SMTP greeting split across multiple chunks.
- Redis PONG response split across multiple chunks.

Both tests failed against the original implementation.

### Fix

Introduced `_recv_line()` to read until a newline is received, the
connection closes, or the configured response-size limit is reached.

### Verification

Both fragmented-response regression tests pass after the fix.

---

## Defect 2: A healthy Compose replica could hide a failed replica

**Fix commit:** `4adee75`

**Affected code:** `src/mailcow_doctor/checks.py`

### Original behavior

The implementation stored containers in a dictionary keyed by
Compose service name.

When multiple containers belonged to the same service, the last
container overwrote the previous one.

A healthy replica could therefore hide an exited or unhealthy replica.

### Reproduction

Added `tests/test_duplicate_replicas.py`.

The test supplied:
1. An exited Redis replica.
2. A healthy Redis replica.

The original implementation returned PASS instead of FAIL.

Reversing the order exposed the overwrite behavior.

### Fix

Changed service evaluation to retain and evaluate every replica.

The service receives the worst status among its replicas.

### Verification

Regression tests cover both replica orderings and the case where
all replicas are healthy.

---

## Defect 3: Valid JSON with an invalid record structure was accepted

**Fix commit:** `5bd1c8c`

**Affected code:** `src/mailcow_doctor/checks.py`

### Original behavior

The parser accepted valid JSON values such as:
- A number: `42`
- A string: `"unexpected"`
- An array containing a mixture of objects and numbers.

These values are valid JSON but are not valid Docker Compose
container records.

Downstream code expects dictionaries and could fail unexpectedly
when accessing container fields.

### Reproduction

Added `tests/test_malformed_compose.py`.

Three cases were tested:
- JSON number.
- JSON string.
- Array containing a non-object record.

All three tests failed against the original parser because it
did not reject these structures.

### Fix

Added explicit structural validation.

The parser now accepts:
- A JSON object.
- An array containing only JSON objects.
- Newline-delimited JSON objects.

Invalid record structures raise ValueError.

### Verification

All three malformed-input regression tests pass after the fix.

---

## Summary

| Defect | Regression test | Fix commit |
|---|---|---|
| Fragmented TCP responses | `test_fragmented_protocols.py` | `75b07b4` |
| Duplicate service replicas | `test_duplicate_replicas.py` | `4adee75` |
| Invalid Compose JSON records | `test_malformed_compose.py` | `5bd1c8c` |

These defects were identified through behavioral testing rather than
naming, formatting or style review.
