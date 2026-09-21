# Extraction Examples

This file shows real-style developer conversation snippets and the exact
structured records that the `engineering-context-curator` skill should produce.
These examples define the extraction quality bar.

---

## Example 1: Architecture Decision

### Conversation Input
> "We need a place to store the ML models. I was thinking about Azure Blob Storage,
> but the PLC has no internet access in most deployments. We also looked at Redis
> but that needs a network connection too. So we ended up going with local disk
> cache with S3 as the source of truth for the build server side."

### Extracted Records

**ADR:**
```markdown
## ADR-001: Use Local Disk Cache with S3 as Source of Truth

**Decision:** Store ML model packages in local disk cache on the PLC;
  use S3 as the authoritative source on the build server.
**Reason:** PLC operates in offline or air-gapped environments where network
  access to external storage services is unavailable.
**Alternatives Considered:**
  - Azure Blob Storage — Requires network connectivity, unavailable on offline PLCs.
  - Redis — Requires network connection, incompatible with offline runtime.
**Status:** Accepted
**Session:** Initial architecture session
```

**Rejected Solutions:**
```markdown
## Rejected: Azure Blob Storage

**Considered For:** ML model package storage
**Why Rejected:** PLC runtime has no internet access in most deployments.
**Session:** Initial architecture session
**Can Reconsider:** Conditional on cloud-connected deployment variant.
```

```markdown
## Rejected: Redis Cache

**Considered For:** ML model package storage
**Why Rejected:** Requires persistent network connection; incompatible with
  offline PLC operation.
**Session:** Initial architecture session
**Can Reconsider:** Conditional on moving to cloud-only deployment.
```

---

## Example 2: Constraint Extraction

### Conversation Input
> "The target hardware is an ARM-based PLC with only 256MB RAM. We can't use any
> external database and it has to run fully offline."

### Extracted Records

```markdown
## Constraint: ARM PLC Hardware

**Limit:** Target runtime is ARM-based PLC architecture.
**Type:** Hardware | Platform
**Non-negotiable:** Yes
**Source:** Hardware specification
**Impact:** Any x86-only binaries or packages will not execute on the target device.
```

```markdown
## Constraint: 256MB RAM Maximum

**Limit:** Maximum available RAM on target PLC is 256MB.
**Type:** Memory
**Non-negotiable:** Yes
**Source:** Hardware specification
**Impact:** Model packages and runtime must fit within this budget;
  large in-memory caches will cause OOM failures.
```

```markdown
## Constraint: Offline Operation

**Limit:** PLC must operate with zero network connectivity.
**Type:** Network
**Non-negotiable:** Yes
**Source:** Deployment environment requirement
**Impact:** All model retrieval must be from local disk; any network call
  will fail at runtime.
```

```markdown
## Constraint: No External Database

**Limit:** No external database may be used for model or state storage.
**Type:** Platform
**Non-negotiable:** Yes
**Source:** Offline operation + hardware constraint
**Impact:** State and versioning must be managed via local filesystem only.
```

---

## Example 3: Open Design Questions

### Conversation Input
> "We haven't decided how rollback will work yet. If a model is corrupted during
> download, we need some way to detect it — maybe checksums? — but we haven't
> nailed that down. Memory pressure testing is also still undefined."

### Extracted Records

```markdown
## Open Issue: Rollback Strategy

**Full Question:** What is the rollback mechanism when a newly deployed model
  fails validation or causes runtime errors?
**Status:** Unresolved
**Impact of Leaving Unresolved:** Failed model deployments have no recovery
  path; PLC could be left in an inoperable state.
**Raised In:** Initial architecture session
**Assigned To:** Unassigned
```

```markdown
## Open Issue: Corruption Detection During Download

**Full Question:** How do we detect model package corruption during the
  download process? Checksum validation was proposed but not designed.
**Status:** Unresolved
**Impact of Leaving Unresolved:** Corrupted packages may be silently installed,
  causing unpredictable runtime failures.
**Raised In:** Initial architecture session
**Assigned To:** Unassigned
```

```markdown
## Open Issue: Memory Pressure Testing

**Full Question:** What is the test plan for validating model loading and
  execution under the 256MB RAM constraint?
**Status:** Unresolved
**Impact of Leaving Unresolved:** Memory overruns will not be caught until
  production deployment on actual PLC hardware.
**Raised In:** Initial architecture session
**Assigned To:** Unassigned
```

---

## Example 4: Validation Standards

### Conversation Input
> "We've been burned by mocks before. From now on, all tests must use real S3
> buckets and real ML packages at production sizes. Mocks are only allowed if
> explicitly requested and approved."

### Extracted Records

```markdown
## Standard: Use Real S3 in All Tests

**Rule:** All tests that interact with S3 must use a real S3 bucket.
  Mocked S3 is not permitted unless explicitly approved per test case.
**Applies To:** Testing | CI
**Rationale:** Mocked S3 previously masked compatibility failures that only
  surfaced in production, causing significant debugging overhead.
**Exceptions:** NONE unless explicitly approved per test case.
```

```markdown
## Standard: Use Real ML Packages at Production Size

**Rule:** All integration and system tests must use real ML model packages
  at production artifact sizes.
**Applies To:** Testing | CI
**Rationale:** Small or synthetic artifacts have hidden memory and latency
  characteristics that differ from production packages.
**Exceptions:** Unit tests for pure logic may use minimal stubs with
  explicit justification.
```

---

## Example 5: Risk Identification

### Conversation Input
> "One thing I'm worried about is that large model packages could take a very
> long time to download to the PLC over the local network, especially if the
> network is slow."

### Extracted Record

```markdown
## Risk: Large Package Download Latency

**Description:** ML model packages may be large enough to cause unacceptably
  long download times over the local PLC network, especially on slow links.
**Severity:** Medium
**Likelihood:** High
**Impact:** Deployment operations may time out or block PLC operation during
  the download window.
**Mitigation:** NONE currently. Potential approaches: chunked download,
  background pre-fetching, delta updates.
**Status:** Open
```

---

## Anti-Pattern Examples

These are extractions that are WRONG and should NOT be produced:

### ❌ Narrative Summary (Wrong)
```
We discussed storage options and decided to use S3 because it works well
for our use case.
```

### ✅ Structured ADR (Correct)
Use the ADR schema from `schemas.md`. Include decision, reason, alternatives,
and status as explicit fields — not embedded in prose.

---

### ❌ Constraint as Preference (Wrong)
```
## Constraint: Prefer PostgreSQL
```

### ✅ Actual Constraint (Correct)
```
## Constraint: No External Database
Non-negotiable: Yes
```
Only hard limits qualify as constraints.

---

### ❌ Rejected Solution Without Reason (Wrong)
```
## Rejected: Redis
Why Rejected: Didn't fit.
```

### ✅ Rejection With Exact Reason (Correct)
```
## Rejected: Redis Cache
Why Rejected: Requires persistent network connection; incompatible with
  offline PLC operation.
```
