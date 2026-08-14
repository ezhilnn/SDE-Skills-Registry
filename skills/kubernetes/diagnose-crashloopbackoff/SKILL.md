# Diagnose CrashLoopBackOff

## Identity
```yaml
name: diagnose-crashloopbackoff
version: 1.0.0
category: kubernetes
maturity: production
risk: medium
mode: advisory
dependencies: [kube API read, pod logs, workload manifests]
```

## Purpose
Determine why a pod is in CrashLoopBackOff using describe/events/logs and the container command. Do not delete or restart production pods to "clear" the loop.

## Activation

### Activation conditions
Activate when a pod, replica set, or workload is reported as CrashLoopBackOff, or restart count is climbing with a crash loop, and kube read access or equivalent logs/events are available.

### Required conditions
Namespace, pod or workload name, and cluster/context identity if multiple contexts exist.

### Non-activation
Do not activate for ImagePullBackOff, ErrImagePull, Pending/unschedulable, CreateContainerConfigError without crashes, or a request to `kubectl delete pod` / rollout restart as the first action. Use image-pull or scheduling skills for those statuses.

### Ambiguous conditions
If the user says "pod is crash looping" but `kubectl get` shows ImagePullBackOff, do not force this skill. If context is unset, ask; do not guess production vs staging from namespace names alone.

## Inputs

### Required
- cluster context (or explicit unknown)
- namespace
- pod or workload name

### Optional
- container name (multi-container pods)
- recent deploy time / image tag
- previous working image
- configmap/secret name referenced by the container (not values)

### Derived
Exit code, restart count, last termination reason, liveness vs command crash, OOMKilled vs error, image digest, failing probe path.

### Sensitive
Kubeconfig, cloud account numbers, secret volumes, environment variables that hold credentials, customer PII in application logs. Redact env values that look like secrets.

## Preconditions
- operations are read-only (`get`, `describe`, `logs`);
- kube context is confirmed or marked unknown-as-production;
- no exec into production as a default diagnostic.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** phase, restart count, image, node, start time.
2. **Relevant source/config:** the container command, args, probes, resource limits from the live pod spec (not necessarily the entire Helm chart).
3. **Logs/events:** current and previous container logs (`--previous` once), warning events on the pod.
4. **Focused history:** last rollout revision only if image/config changed.
5. **Additional context:** node memory pressure, adjacent pods, only if OOM or eviction is implicated.

Do not `kubectl get all -A`. Do not dump every ConfigMap in the namespace.

## Tool Requirements

### kubectl get/describe
- **Purpose:** status, events, last state, exit code.
- **Allowed:** `get pod -o yaml` / `describe pod` for the named object; `get events --field-selector involvedObject.name=...`.
- **Forbidden:** `delete`, `edit`, `scale`, `rollout restart`, `drain`.
- **Expected output:** Last State, Reason, Exit Code, OOMKilled, probe failures.
- **Failure behavior:** mark kube API blocked.

### kubectl logs
- **Purpose:** crash output.
- **Allowed:** logs for the named container, including `--previous` once; tail/limit-bytes to bound size.
- **Forbidden:** following logs indefinitely; dumping all containers in the namespace.
- **Expected output:** stack trace, panic, missing file, bind error, migration error.
- **Failure behavior:** continue with describe/events.

### Manifest inspection
- **Purpose:** command, probes, envFrom.
- **Allowed:** read the live pod spec and the matching Deployment/CronJob snippet.
- **Forbidden:** applying a patched manifest to production.
- **Expected output:** likely crash preconditions.
- **Failure behavior:** use live spec only.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

## Security Boundaries

### Allowed
- read pod spec, events, logs;
- compare image tag/digest to a known good;
- recommend a spec or application fix.

### Forbidden
- deleting pods, nodes, or workloads;
- exec/debug containers in production unless a separately authorized skill and approval exist;
- reading secret object values;
- changing RBAC, PSP/PSA, or network policy to "get access";
- disabling liveness probes to hide the loop.

### Approval gate
Any restart, image bump in cluster, secret rotation, or probe change in a live environment requires explicit approval.

## Secret Handling
Redact `env` values and secret names' contents. If logs print a connection string, report exposure without reproducing it.

## Execution Workflow

### 1. Understand
Confirm CrashLoopBackOff (not pull/pending), namespace, pod, container, context.

### 2. Establish baseline
Restart count, last exit code, image, when it started looping versus last healthy replica.

### 3. Collect evidence
1. `Last State.Reason` and exit code;
2. previous logs;
3. current logs if still restarting;
4. probes vs command (did it ever become ready?);
5. resource limits if Reason is OOMKilled.

### 4. Form hypotheses
- application panic / uncaught exception on boot;
- missing config or file;
- failed DB migration or dependency at startup;
- liveness probe killing a slow-start process;
- OOMKilled;
- command/args wrong (shell vs exec form);
- crashing init completed but app container fails (init is a different status — re-check).

### 5. Rank hypotheses
Exit code 137 + OOMKilled outranks "app bug" until memory is checked. Probe kills have `Last Terminate` from kubelet with probe messages in events.

### 6. Test the highest-signal hypothesis
One bounded log read or describe field. Do not restart the pod as a test.

### 7. Re-evaluate
If logs are empty, check if the process is killed before logging (OOM, exec format error).

### 8. Identify result status
- **CONFIRMED:** exit reason + log line or OOMKilled flag.
- **LIKELY:** strong events, logs incomplete.
- **UNCONFIRMED:** crash without usable logs.
- **BLOCKED:** no kube/log access.
- **NOT_REPRODUCED:** pod is Running and Ready now.
- **NO_ISSUE_FOUND:** status was misread (not CrashLoopBackOff).

### 9. Recommend remediation
Smallest spec or application change. Do not recommend removing probes as the fix unless evidence shows probe misconfiguration, and even then as a spec correction with approval.

### 10. Verify
Pod reaches Ready and restart count stabilizes on new ReplicaSet. Live verification is observed, not inferred from a YAML edit.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
```text
IF reason is OOMKilled:
    do not prefer application exception as confirmed cause
IF events show Liveness probe failed and process is still starting:
    rank probe/startupProbe misconfig high
IF exit code is 1/2 with a stack trace:
    rank application/config high
IF logs empty and exit is 137:
    rank OOM or SIGKILL
IF context unknown:
    treat cluster as production
```

## Failure Handling
- Missing namespace: ask.
- kubectl auth error: BLOCKED, do not switch contexts speculatively.
- Logs empty: use previous logs and termination reason; do not invent a stack trace.
- Conflicting: one replica looping, others healthy → instance/config/node hypothesis, not cluster-wide conclusion.

## Stop Conditions
Stop when cause is evidenced, access is blocked, status is not CrashLoopBackOff, or the operator demands a production delete/restart.

## Verification
Classify Observed / Verified / Inferred / Recommended. A recommended image bump is not verified until Ready is observed.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <pod/workload CrashLoopBackOff>
Findings:
  - <exit code, reason, restart count>
Evidence:
  - <describe/logs/events>
Root Cause: <confirmed or ranked>
Impact: <availability of the workload>
Recommended Action: <spec or app fix; no unapproved restart>
Risk: <MEDIUM|HIGH>
Verification: <Ready and stable restart count>
Remaining Uncertainty: <empty logs, unknown context>
```

## Examples

### Valid example
`payments` pod in `prod` restarts 18 times. Last State OOMKilled, limit 128Mi, logs show heap growth then silence.

Expected result: **CONFIRMED** memory limit / leak hypothesis with OOMKilled evidence.

### Invalid example
Pod is `ImagePullBackOff` for a private registry.

Do not activate this skill.

### Edge case
CrashLoopBackOff with empty logs and exit code 1. Binary might be crashing before stdio flush.

Expected result: **UNCONFIRMED** application/config; recommend increasing log buffering or a non-prod reproduction; do not delete the pod.

### Safety example
"Just kubectl delete pod so it comes back clean."

Refuse. Restarting does not diagnose CrashLoopBackOff and is a production mutation.

## Evaluation Criteria
- **Activation accuracy:** CrashLoopBackOff only.
- **Rejection accuracy:** rejects pull/pending and delete-first requests.
- **Correctness:** uses Last State + logs; OOM vs app distinguished.
- **Safety:** read-only kube, no secret dumps, no unapproved restarts.
- **Efficiency:** named pod only, bounded logs.
- **Verification:** Ready observed, not assumed.
- **Robustness:** empty logs do not become invented panics.
- **Human usefulness:** exit code, reason, and smallest fix.
