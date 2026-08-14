# CrashLoopBackOff

Complements `diagnose-crashloopbackoff`.

## Problem
A pod restarts until kubelet backs off.

## Symptoms
`CrashLoopBackOff`, climbing restart count, Ready 0.

## Prerequisites
Read access to the named namespace. Confirmed kube context.

## Diagnosis
1. Confirm the status is CrashLoopBackOff, not ImagePullBackOff or Pending.
2. Read Last State reason and exit code.
3. Read previous logs once, bounded.
4. Distinguish OOMKilled, probe kill, and application exit.

## Commands

```bash
kubectl describe pod -n <ns> <pod>
kubectl logs -n <ns> <pod> -c <container> --previous --tail=200
```

Do not `kubectl delete pod` as diagnosis.

## Interpretation
- OOMKilled / 137 → memory
- Events: Liveness probe failed → probe vs slow start
- Exit 1 + stack trace → application/config

## Common Causes
Panic on boot, missing config, bad command/args, too-low memory limit, probe too aggressive, failed migration.

## Resolution
Fix image, config, limits, or probes via a normal rollout. Restarts without a change will loop again.

## Verification
New ReplicaSet Ready; restart count stable.

## Prevention
startupProbe for slow boots, memory requests/limits based on observed heap, logging before first crash path.

## Related Skills
`diagnose-crashloopbackoff`, `diagnose-image-build-failure`
