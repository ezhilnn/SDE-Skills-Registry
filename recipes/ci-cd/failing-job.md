# Failing CI Job

Complements `diagnose-failing-ci-job`.

## Problem
A named workflow job is red.

## Symptoms
Required check failing, merge blocked, red main.

## Prerequisites
Job name, SHA, log access.

## Diagnosis
1. Open the failing step, not the workflow summary alone.
2. Find the first hard error, not the last retry line.
3. Compare to the last green run of the same job.
4. Map the error to test vs compile vs install vs infra vs deploy.

## Commands

```bash
# GitHub example — read-only
gh run view <run-id> --log-failed
git show --stat <sha>
```

## Interpretation
Install/lockfile errors after a dependency bump are usually the bump. `exit code 1` with no inner error is incomplete evidence.

## Common Causes
Failed assertion, missing module, action pin change, cache, runner image, expired OIDC, OOM on the runner.

## Resolution
Fix the command or the code. Do not disable required checks. Do not echo secrets.

## Verification
The same job is green on a SHA that contains the fix.

## Prevention
Pin actions by SHA, cache keys that include lockfiles, keep install and test logs distinct.

## Related Skills
`diagnose-failing-ci-job`, `investigate-flaky-test`, `diagnose-image-build-failure`
