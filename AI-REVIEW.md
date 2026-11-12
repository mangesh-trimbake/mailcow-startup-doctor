# AI Code Review

This document records three defects identified during AI-assisted code review and testing. Each issue was reproduced with a test before the corresponding fix was applied.

## 1. Fragmented TCP responses

**Problem:** The original protocol checks used a single `recv(1024)` call and assumed the complete server response would arrive in one read.

**Why it matters:** TCP is a stream protocol. A response can arrive in multiple chunks, so reading only once can produce an incomplete response and an incorrect failure.

**Reproduction:** Added tests using a fake socket that returns a protocol response in multiple chunks.

**Fix:** Introduced `_recv_line()` to read until a newline, EOF, or the configured maximum size.

**Commit:** `75b07b4` — Fix protocol probes handling fragmented TCP responses.

**Test:** `tests/test_fragmented_protocols.py`

## 2. Failed replicas hidden by healthy replicas

**Problem:** Compose service results were stored by service name. When multiple containers represented the same service, a later healthy replica could overwrite an earlier failed replica.

**Why it matters:** The diagnostic tool could incorrectly report a service as healthy even when one of its replicas was failing.

**Reproduction:** Added tests with one healthy and one failed replica, testing both input orders.

**Fix:** Evaluate every replica and aggregate the results using the worst status.

**Commit:** `4adee75` — Prevent healthy Compose replicas hiding failed replicas.

**Test:** `tests/test_duplicate_replicas.py`

## 3. Malformed Docker Compose JSON records

**Problem:** The original parser accepted JSON structures without strictly validating that each record was an object representing a Compose container.

**Why it matters:** Unexpected JSON values could enter the evaluation logic and cause confusing results or runtime errors.

**Reproduction:** Added tests for scalar JSON values, arrays containing non-object values, and malformed newline-delimited records.

**Fix:** Validate the top-level JSON structure and every record. Raise a clear `ValueError` for invalid input.

**Commit:** `5bd1c8c` — Reject malformed Docker Compose JSON records.

**Test:** `tests/test_malformed_compose.py`

## Review takeaway

These issues showed that diagnostic code needs to handle imperfect real-world inputs, not just the happy path. The fixes were accompanied by regression tests so that the same defects are less likely to return.
