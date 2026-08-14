# Intermittent HTTP 500

Human procedure that complements `investigate-intermittent-http-500`. The skill is the agent workflow; this recipe is the operator checklist.

## Problem
A service returns HTTP 500 for a subset of requests.

## Symptoms
- Error rate above baseline but far from 100%
- User reports that retry sometimes works
- Alerts on 5xx ratio, not on total outage

## Prerequisites
Read-only logs, metrics, and traces. Endpoint and time window. At least one correlation id.

## Diagnosis
1. Confirm the failure is 5xx and not 4xx or a client timeout mislabeled as 500.
2. Compare error rate to a nearby healthy window.
3. Slice by instance, version, region, and dependency.
4. Open one failing trace before reading application source.
5. Compare one success and one failure with the same endpoint.

## Commands
Use your platform's equivalents. Do not paste secrets from headers.

```text
# Conceptual queries — replace with the actual observability backend
error_rate(endpoint, window) vs baseline
count by (pod, version, status)
trace(request_id).failed_span
```

## Interpretation
- One pod only → instance health, limits, or local disk
- One version only → bad deploy
- All pods, one dependency → downstream
- Specific payload shape → data-dependent exception

Correlation is not confirmation.

## Common Causes
Connection pool exhaustion, dependency timeouts, race conditions, bad canary, resource limits, nil/null on rare branches.

## Resolution
Smallest change that matches evidence. Production restart/rollback is a separate authorized change.

## Verification
5xx ratio returns to baseline; the exception signature disappears; the implicated version no longer correlates.

## Prevention
SLOs on 5xx, saturation metrics on pools, canary analysis, tests for the failing payload class.

## Related Skills
`investigate-intermittent-http-500`
