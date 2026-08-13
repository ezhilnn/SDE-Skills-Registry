# Investigate Intermittent HTTP 500 Responses

## Identity
```yaml
name: investigate-intermittent-http-500
version: 1.0.0
category: debugging
maturity: production
risk: medium
mode: advisory
dependencies: [application logs, metrics or traces, relevant source/configuration]
```

## Purpose
Determine the most strongly supported cause of intermittent HTTP 500 responses using focused, read-only evidence collection. Never present an assumption as a confirmed root cause.

## Activation

### Activation conditions
Activate when:
- the symptom is HTTP 500 or equivalent server-side failure;
- failures are intermittent or limited to a subset of requests, instances, versions, regions, inputs, or times;
- at least one request-level or application-level evidence source is available.

### Required conditions
Establish the endpoint or operation, approximate failure window, and at least one failing request identifier, timestamp, trace ID, or equivalent correlation key when available.

### Non-activation
Do not activate when every request fails consistently, the primary symptom is 4xx, the problem is a build/deployment failure, or the requested work is production remediation rather than diagnosis. Use a consistently-failing HTTP 500 workflow in those cases.

### Ambiguous conditions
Ask for clarification when intermittent behavior cannot be distinguished from insufficient sampling, or the endpoint/time window cannot be established.

## Inputs

### Required
- endpoint or operation
- failure window
- known failing example(s)

### Optional
- successful examples
- request/trace IDs
- error payload metadata
- deployment/change history
- instance/pod/version/region identifiers
- dependency health metrics
- latency and error-rate metrics
- relevant configuration changes

### Derived
The agent may calculate failure rate by time bucket, instance, deployment version, region, or dependency and compare successful versus failed requests.

### Sensitive
Treat tokens, cookies, authorization headers, personal data, database credentials, and production identifiers as sensitive. Do not unnecessarily request, print, or reproduce them. Redact secrets from evidence.

## Preconditions
- diagnostic access is read-only;
- the investigation window is narrow enough for targeted search;
- observations, hypotheses, evidence, and conclusions can be kept separate.

If a diagnostic source is unavailable, continue only with available evidence and explicitly mark the affected conclusion as unverified or blocked.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** endpoint, window, failure rate/count, failing examples.
2. **Relevant source/config:** request handling, error mapping, dependency calls, timeout/retry/circuit-breaker logic.
3. **Logs/metrics/traces:** matching errors, successful comparisons, latency, instance/version/region, dependency health.
4. **Focused history:** recent deployment or configuration changes only when evidence suggests a change correlation.
5. **Additional context:** load only when a targeted hypothesis cannot be tested with existing evidence.

Never ingest the entire repository or complete log history without evidence-based justification.

## Tool Requirements

### Log search
- **Purpose:** locate matching 500 responses and exception signatures.
- **Allowed:** read/search/filter by endpoint, timestamp, trace ID, instance, version, severity.
- **Forbidden:** deleting logs, changing retention, exposing secrets.
- **Expected output:** timestamped errors and useful correlation dimensions.
- **Failure behavior:** mark logs unavailable and continue.

### Metrics
- **Purpose:** correlate failure rate, latency, saturation, and dependency health.
- **Allowed:** read time-series metrics and aggregate by relevant dimensions.
- **Forbidden:** changing alerts, thresholds, dashboards, or service configuration.
- **Expected output:** correlations that distinguish hypotheses.
- **Failure behavior:** mark metric-based hypotheses unverified.

### Traces
- **Purpose:** inspect failing request execution paths.
- **Allowed:** read sampled traces and spans.
- **Forbidden:** modifying tracing configuration or exporting sensitive payloads.
- **Expected output:** failed span, timing, upstream/downstream failure, retry behavior.
- **Failure behavior:** continue with other evidence.

### Source/configuration inspection
- **Purpose:** identify code paths capable of producing intermittent failures.
- **Allowed:** read relevant code, configuration, dependency declarations, and focused diffs.
- **Forbidden:** modifying files or runtime configuration.
- **Expected output:** candidate failure paths and their preconditions.
- **Failure behavior:** mark code-based hypotheses incomplete.

### Deployment/version history
- **Purpose:** correlate failures with a release or configuration version.
- **Allowed:** read deployment metadata and history.
- **Forbidden:** rollback, redeploy, restart, or otherwise mutate production.
- **Expected output:** version-to-failure correlation.
- **Failure behavior:** omit release correlation and continue.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

This skill performs diagnosis only. Production changes require a separately authorized execution workflow.

## Security Boundaries

### Allowed
- read source code, logs, metrics, and traces;
- inspect deployment metadata;
- run read-only diagnostics;
- compare redacted failing and successful requests.

### Forbidden
- modifying production code/configuration/infrastructure;
- deleting or mutating production data;
- changing IAM permissions;
- bypassing authentication or authorization;
- disabling security or monitoring controls;
- exposing credentials or tokens;
- restarting, redeploying, or rolling back production services.

### Approval gate
Any destructive or externally impactful diagnostic/remediation action must be handed off to an authorized controlled-execution workflow with explicit approval.

## Secret Handling
- Never print secrets.
- Never commit credentials into generated output.
- Redact authorization headers, API keys, cookies, passwords, connection strings, and tokens.
- Use placeholders such as `<ACCESS_TOKEN>` and `<DATABASE_URL>`.
- If a tracked file appears to contain a secret, report that fact without reproducing the value.

## Execution Workflow

### 1. Understand
Confirm endpoint, time window, intermittent nature, and known failing/successful examples.

### 2. Establish baseline
Compare failure rate and latency during the incident with a nearby healthy window.

### 3. Collect evidence
Start with failing request identifiers. Collect, in order:
1. application exception/stack signature;
2. trace failure location;
3. instance/pod/version/region dimensions;
4. dependency calls immediately preceding failure;
5. timeout/retry/circuit-breaker signals.

### 4. Form hypotheses
Consider evidence-backed candidates such as:
- one unhealthy instance or pod;
- a defective deployment version;
- dependency timeout or partial outage;
- connection-pool/resource exhaustion;
- concurrency/race condition;
- data-dependent application exception;
- configuration drift;
- load-related saturation.

### 5. Rank hypotheses
Rank by direct evidence, correlation strength, reproducibility, and independent supporting sources.

### 6. Test the highest-signal hypothesis
Use the cheapest read-only check that can distinguish competing hypotheses. Prefer focused dimensions such as pod/version/dependency before broad repository inspection.

### 7. Re-evaluate
Reject hypotheses contradicted by evidence. Increase confidence only when evidence supports them.

### 8. Identify result status
- **CONFIRMED:** direct evidence establishes the cause.
- **LIKELY:** multiple strong signals support the cause but direct confirmation is unavailable.
- **UNCONFIRMED:** plausible causes remain.
- **BLOCKED:** necessary evidence/access is unavailable.
- **NOT_REPRODUCED:** symptom could not be reproduced and evidence is insufficient.
- **NO_ISSUE_FOUND:** available evidence indicates normal behavior.

### 9. Recommend remediation
Recommend the smallest appropriate corrective action. Do not execute production changes.

### 10. Verify
Define observable success criteria such as 500 rate returning to baseline, exception signatures disappearing, affected versions no longer correlating with errors, or dependency timeout rates returning to normal.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
Use concise evidence-based rules:
```text
IF evidence supports a hypothesis:
    increase confidence
IF evidence contradicts a hypothesis:
    reject it
IF evidence is insufficient:
    collect one targeted high-signal check
IF multiple hypotheses remain:
    rank them and state uncertainty
IF only correlation exists:
    do not label the cause confirmed
```
Do not expose private chain-of-thought; provide concise reasoning summaries tied to observable evidence.

## Failure Handling
- **Missing input:** state what is missing and stop if safe investigation cannot continue.
- **Tool unavailable:** continue with available read-only sources and mark affected conclusions unverified.
- **Command/query failure:** record the failed step, never invent output, and try one alternative read-only method when appropriate.
- **Insufficient permissions:** do not bypass them; mark the evidence source blocked.
- **Conflicting evidence:** preserve the conflict and lower confidence rather than choosing a convenient explanation.
- **Unknown environment:** establish environment explicitly; do not infer production/staging/local from naming alone.
- **Cannot reproduce:** use historical evidence and mark live reproduction as not achieved.
- **Multiple possible causes:** provide a ranked set and state what evidence would distinguish them.

## Stop Conditions
Stop when:
- the root cause is sufficiently supported by independent evidence;
- evidence is contradictory and requires human investigation;
- required permissions are unavailable;
- further investigation has diminishing value;
- proposed action exceeds skill permissions;
- required context cannot be safely obtained.

## Verification
Classify findings as:
- **Observed:** directly retrieved evidence.
- **Verified:** independently confirmed by a diagnostic check.
- **Inferred:** supported interpretation that is not directly proven.
- **Recommended:** proposed next action.

Never label an inference as verified.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <concise symptom>
Findings:
  - <finding>
Evidence:
  - <observation and source>
Root Cause: <confirmed cause or best-ranked hypothesis>
Impact: <known or estimated impact>
Recommended Action: <smallest appropriate remediation>
Risk: <LOW|MEDIUM|HIGH|CRITICAL>
Verification: <observable verification condition>
Remaining Uncertainty: <what remains unproven>
```

## Examples

### Valid example
An API normally returns 200 but about 2% of requests return 500. Failures occur only on two pods running the newest version, and their traces show connection-pool exhaustion while healthy pods do not.

Expected result: **LIKELY** or **CONFIRMED** depending on whether resource exhaustion is directly verified.

### Invalid example
Every request returns 500 immediately after a deployment.

Do not activate this skill; use a consistently-failing HTTP 500 workflow.

### Edge case
Failures occur only for requests containing a customer-created configuration, but logs do not safely expose enough of that configuration to investigate.

Expected result: report a data-dependent hypothesis as unconfirmed and identify the missing evidence.

### Safety example
The leading hypothesis could be tested by restarting a production pod.

Do not restart it. Return the action as a separately authorized controlled-execution step requiring explicit approval.

## Evaluation Criteria
- **Activation accuracy:** activates for genuinely intermittent 500 failures and rejects consistently failing or unrelated incidents.
- **Rejection accuracy:** rejects 4xx, build failures, and remediation-only requests.
- **Correctness:** uses independent evidence when available and distinguishes correlation from causation.
- **Safety:** remains read-only and protects secrets and production state.
- **Efficiency:** starts with failing request identifiers and high-signal dimensions instead of broad context.
- **Verification:** provides an observable verification criterion.
- **Robustness:** handles missing, conflicting, unavailable, and non-reproducible evidence without fabrication.
- **Human usefulness:** produces a diagnosis an experienced SDE can validate and hand to an authorized remediation workflow.
