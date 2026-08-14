# Investigate a Flaky Test

## Identity
```yaml
name: investigate-flaky-test
version: 1.0.0
category: testing
maturity: production
risk: medium
mode: advisory
dependencies: [test runner, failing/passing artifacts, source of the test]
```

## Purpose
Determine why a specific test both passes and fails without an intentional product change, using timing, isolation, and shared-state evidence. Do not quarantine by skipping in required CI without approval.

## Activation

### Activation conditions
Activate when the same test identifier has both pass and fail results across runs, retries, or shards, and logs or the test source are available.

### Required conditions
Test identifier (file + name), and at least two outcomes (pass and fail) or a retry that failed then passed.

### Non-activation
Do not activate when the test always fails (use `diagnose-failing-ci-job` or a deterministic test-fix workflow), when the product is broken in all environments, or when the request is `skip` / `xit` / `allow_failure` on a required suite.

### Ambiguous conditions
If only one failure exists, ask whether it reproduced. If the name changed between runs, do not assume identity.

## Inputs

### Required
- test identifier
- pass and fail evidence (logs, CI attempts, local reruns)

### Optional
- seed / shard / worker index
- timestamps, duration
- fixture and container setup
- related product change SHA (to distinguish flake vs regression)

### Derived
Failure signature variance, timing, order dependence, clock/timezone, network, leaked goroutines/threads, unique constraint collisions.

### Sensitive
PII in test fixtures, production credentials mistakenly used in tests. Never point tests at production to "make them stable".

## Preconditions
- prefer local reproduction with the same seed/shard;
- do not delete assertions;
- do not use production data stores.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** test name, fail rate, duration, shard/worker.
2. **Relevant source:** the test and its immediate fixtures/helpers.
3. **Logs:** failing assertion vs passing run of the same test.
4. **Focused history:** recent edits to this test or its dependency.
5. **Additional context:** global setup, other tests in the file, only if order dependence is implicated.

Do not read the entire test suite.

## Tool Requirements

### test runner
- **Purpose:** reproduce isolation vs order.
- **Allowed:** run the single test repeatedly; run the file; run with a known seed.
- **Forbidden:** `--no-verify` of TLS to hit production; infinite loops of the full suite without bound.
- **Expected output:** fail rate, signature.
- **Failure behavior:** use CI history only; mark local reproduction not achieved.

### CI history
- **Purpose:** fail rate and shard correlation.
- **Allowed:** read jobs for this test name.
- **Forbidden:** deleting retries to hide flakes.
- **Expected output:** pattern by shard/time/OS.
- **Failure behavior:** continue with source.

### source inspection
- **Purpose:** shared mutable state, sleeps, time, randomness, live network.
- **Allowed:** read test + helper.
- **Forbidden:** weakening assertions as the fix.
- **Expected output:** flake mechanism candidates.
- **Failure behavior:** UNCONFIRMED.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

A test patch may be recommended. Skipping required tests is assisted/controlled, not this skill's default.

## Security Boundaries

### Allowed
- run tests in disposable environments;
- recommend isolation, fake clocks, unique keys, retries at the *infrastructure* only when the product retry is already specified.

### Forbidden
- skipping required tests;
- using production databases or live customer accounts;
- increasing timeouts indefinitely to hide races;
- committing `sleep(10)` as a root-cause fix without evidence.

### Approval gate
Quarantine lists, `continue-on-error`, or removing a test from required CI need explicit approval.

## Secret Handling
Do not embed real credentials in test fixtures. Use `<API_KEY>` placeholders.

## Execution Workflow

### 1. Understand
Confirm the test ID and that outcomes actually differ.

### 2. Establish baseline
Fail rate, duration distribution, last deterministic period.

### 3. Collect evidence
1. assertion message variance;
2. same SHA pass/fail (true flake) vs fail only after a commit (regression);
3. time, random, network, filesystem, clock;
4. shared module state / singleton / DB rows with fixed IDs.

### 4. Form hypotheses
- order dependence / leaked state;
- race / missing wait for async;
- time/timezone/DST;
- collision on unique keys;
- real network / rate limit;
- overloaded runner (timeouts only under load);
- non-deterministic product bug (still a product defect, not "just a flake").

### 5. Rank hypotheses
Same SHA pass/fail ranks flake/race over "the new feature is wrong", but a product race is a valid root cause.

### 6. Test the highest-signal hypothesis
Run the test in isolation vs after a suspected sibling test; or freeze time; bound the experiment.

### 7. Re-evaluate
If isolation always passes and the file fails, rank order dependence higher.

### 8. Identify result status
- **CONFIRMED:** mechanism reproduced (e.g. fails after test B).
- **LIKELY:** source pattern matches, reproduction incomplete.
- **UNCONFIRMED:** fail rate known, mechanism not shown.
- **BLOCKED:** cannot get logs or source.
- **NOT_REPRODUCED:** cannot flake locally or in bounded reruns.
- **NO_ISSUE_FOUND:** always passes; original fail was a broken environment.

### 9. Recommend remediation
Fix isolation or product race. Do not recommend skip. Bounded retries in the runner are a mitigation, not a root-cause fix — label them as such.

### 10. Verify
N bounded reruns of isolation and file/suite order, plus CI on the fix SHA. State N. Do not claim "flake gone" after one pass.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
```text
IF same SHA both passes and fails:
    rank non-determinism; still decide test vs product
IF only fails after a SHA:
    rank regression; this skill may yield to CI diagnosis
IF sleep appears to "fix" it:
    treat as evidence of a race, not as the solution
IF unique constraint errors:
    rank fixed IDs / parallel workers high
```

## Failure Handling
- Cannot rerun: use CI artifacts; lower confidence.
- Conflicting signatures: multiple causes; do not pick one.
- Environment-only timeouts: LIKELY runner saturation; do not rewrite the product without more evidence.

## Stop Conditions
Stop when the mechanism is reproduced, reruns are not reproducing and budget is exhausted, or the operator demands a skip.

## Verification
Rerun counts are observed. "Should be stable" is inferred.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <test id and fail rate>
Findings:
  - <isolation vs race vs data vs time>
Evidence:
  - <logs, reruns, source>
Root Cause: <confirmed mechanism or ranked>
Impact: <CI reliability, hidden product race>
Recommended Action: <fix isolation/product; no skip>
Risk: <MEDIUM>
Verification: <N reruns + CI SHA>
Remaining Uncertainty: <unreproduced, load-only>
```

## Examples

### Valid example
`OrdersTest.creates_invoice` fails ~10% on SHA `abc`. Isolation passes 50/50; the file fails when `deletes_all_orders` runs first.

Expected result: **CONFIRMED** order dependence / shared DB rows.

### Invalid example
`OrdersTest.creates_invoice` has failed every run since the last commit.

Do not activate this skill as a flake investigation.

### Edge case
Fails only on shard 7 at 08:00 UTC Mondays.

Expected result: **LIKELY** time or shared-resource hypothesis; do not skip; collect timezone/cron evidence.

### Safety example
"Add xit and we'll come back to it after the release."

Do not skip a required test. Offer a separately approved quarantine process if the organization has one.

## Evaluation Criteria
- **Activation accuracy:** pass/fail of the same test.
- **Rejection accuracy:** always-fail and skip-requests.
- **Correctness:** distinguishes test isolation vs product race.
- **Safety:** no production targets, no silent skip.
- **Efficiency:** single test then file, not full suite first.
- **Verification:** stated rerun count.
- **Robustness:** unreproduced flakes stay NOT_REPRODUCED.
- **Human usefulness:** names the mechanism and a real fix.
