# Diagnose a Failing CI Job

## Identity
```yaml
name: diagnose-failing-ci-job
version: 1.0.0
category: ci-cd
maturity: production
risk: medium
mode: advisory
dependencies: [CI job logs, workflow definition, failing SHA]
```

## Purpose
Identify the most strongly supported cause of a specific CI job or step failure using the failing log region and the workflow definition. Do not "fix CI" by disabling required checks.

## Activation

### Activation conditions
Activate when:
- a named workflow, job, or step has failed;
- a failing SHA, run URL, or log artifact is available or can be fetched read-only;
- the operator wants diagnosis (and optionally a patch recommendation).

### Required conditions
Job or step name, failing git SHA or run identifier, and access to the failure log or an explicit paste of the failing region.

### Non-activation
Do not activate for a test that is flaky across passing and failing runs without a current failed job (use `investigate-flaky-test`), for image build failures where the only log is `docker build` (use `diagnose-image-build-failure` unless the CI wrapper is the failure), or when the request is to skip/disable a required gate.

### Ambiguous conditions
Ask which job/step failed when a pipeline has multiple red jobs. Ask for the failing SHA when local HEAD may not match the CI SHA.

## Inputs

### Required
- job or step identity
- run ID or failing SHA
- failure log or equivalent

### Optional
- workflow YAML path
- previous successful run on the same branch
- changed files in the SHA
- runner labels / OS / container image
- secrets-related error metadata without secret values

### Derived
Failing command, exit code, first error line vs last retry, difference versus last green run, cache hit/miss, coverage of the change in the failing SHA.

### Sensitive
CI secrets, `GITHUB_TOKEN` / deploy keys, OIDC role ARNs with account numbers, customer data in test fixtures. Redact. Do not request secret values to "see if they expired" — ask for rotation status instead.

## Preconditions
- investigation is read-only against CI config and logs;
- local reproduction is optional and must use the CI SHA;
- required-status checks remain enabled.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** workflow, job, step, SHA, exit status, duration.
2. **Relevant source/config:** the workflow YAML for that job and the command that failed.
3. **Logs:** the failing step, plus 50–100 lines around the first error, not the entire raw log if it is huge.
4. **Focused history:** last green run on the same job; diff of the failing SHA limited to files that job uses.
5. **Additional context:** runner image, cache keys, matrix axes only when the error implicates environment.

Never download all artifacts for all jobs. Summarize huge logs after locating the first hard error.

## Tool Requirements

### CI log fetch
- **Purpose:** obtain the failing step output.
- **Allowed:** read job logs for the named run.
- **Forbidden:** deleting logs, rerunning with secrets printed, downloading unrelated artifacts.
- **Expected output:** command, exit code, first error.
- **Failure behavior:** ask for a pasted failing region; do not invent logs.

### Workflow definition
- **Purpose:** see what the step actually runs.
- **Allowed:** read workflow YAML and reusable workflow references used by this job.
- **Forbidden:** committing a skip of the job; weakening `pull_request` triggers to dodge the failure.
- **Expected output:** command, working directory, env, matrix.
- **Failure behavior:** diagnose from logs only and mark YAML unknown.

### Git diff of failing SHA
- **Purpose:** correlate the failure with the change.
- **Allowed:** `git show --stat` and file-limited diffs for files the job touches.
- **Forbidden:** resetting CI branches; force-pushing over the failing SHA.
- **Expected output:** candidate causal files.
- **Failure behavior:** omit change correlation.

### Local reproduction
- **Purpose:** confirm the failing command.
- **Allowed:** run the same command on the failing SHA in a disposable environment.
- **Forbidden:** using production credentials; `curl | bash` installers from the log without review.
- **Expected output:** pass/fail matching CI.
- **Failure behavior:** mark local reproduction not achieved.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

Patches may be proposed. Enabling a skip flag, deleting a required check, or writing production deploy credentials is out of scope.

## Security Boundaries

### Allowed
- read logs, workflow YAML, and the failing SHA;
- recommend a minimal patch or test fix;
- run the failing command locally without production secrets.

### Forbidden
- disabling required status checks or branch protection;
- echoing secrets in workflow YAML (`echo ${{ secrets.* }}`);
- broadening `pull_request_target` checkout of untrusted code;
- installing unpinned binaries from a failed log's suggested curl;
- rerunning deploy jobs against production to "see if it passes".

### Approval gate
Any workflow change that affects deployment, secret access, or required checks requires explicit approval in a separately authorized change.

## Secret Handling
Redact tokens in logs. If a log contains a secret, treat it as an exposure and follow `recover-committed-secret` / rotation guidance without reproducing the value.

## Execution Workflow

### 1. Understand
Name the job/step, SHA, and whether this is a new failure or a known red main.

### 2. Establish baseline
Compare to the last green run of the same job: command, runner image, duration, cache.

### 3. Collect evidence
In order:
1. first non-retry error line and exit code;
2. command that produced it;
3. whether the error is infra (runner, network, registry) vs build vs test vs lint vs deploy;
4. files changed in the SHA that the job uses.

### 4. Form hypotheses
- product test assertion failure;
- compile/type error in changed files;
- missing dependency / lockfile drift;
- flaky test (only if history shows pass/fail on same SHA or no relevant diff);
- cache poisoning or stale cache key;
- runner image or action version change;
- secret/OIDC misconfiguration (no values);
- disk / OOM on the runner.

### 5. Rank hypotheses
Prefer hypotheses that match the first hard error. Infra hypotheses need runner-level evidence, not just "CI is flaky".

### 6. Test the highest-signal hypothesis
One check: YAML command vs log, or local run of that command, or compare action pin to last green.

### 7. Re-evaluate
If the last log lines are retries, walk up to the original error. Do not treat a timeout wrapper as the root cause without the inner error.

### 8. Identify result status
- **CONFIRMED:** command, error, and causal file/config are directly shown.
- **LIKELY:** strong log match, SHA correlation incomplete.
- **UNCONFIRMED:** multiple plausible causes.
- **BLOCKED:** logs or SHA unavailable.
- **NOT_REPRODUCED:** local command passes; CI environment still implicated.
- **NO_ISSUE_FOUND:** job actually succeeded or failure was a cancelled run.

### 9. Recommend remediation
Smallest change that addresses the confirmed error. Do not recommend `continue-on-error: true` for required gates.

### 10. Verify
The same job on the same checks passes on a new SHA that includes the fix. Record that CI green is verified only after the run completes.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
```text
IF first error is an assertion in a test:
    prefer product/test cause over runner cause
IF error is missing secret / 403 to an identity provider:
    do not request the secret value
IF job failed after a cache restore:
    test cache as a hypothesis, do not assume it
IF only the last retry line is visible:
    seek the first failure
IF logs unavailable:
    BLOCKED, do not guess
```

## Failure Handling
- **Missing logs:** BLOCKED.
- **Tool unavailable:** accept a pasted log region.
- **Command failure locally:** record; do not equate local fail with CI cause without SHA match.
- **Insufficient permissions:** cannot read private logs → BLOCKED.
- **Conflicting evidence:** local pass, CI fail → environment hypothesis, NOT_REPRODUCED locally.
- **Unknown environment:** do not assume GitHub-hosted vs self-hosted from job name alone.

## Stop Conditions
Stop when the first hard error is explained with evidence, logs cannot be obtained, the requested action is disabling a gate, or further artifact downloads are low-signal.

## Verification
- **Observed:** log lines, YAML, SHA diff stats.
- **Verified:** local or CI re-run of the same job (only if it actually ran).
- **Inferred:** "probably the cache".
- **Recommended:** pin, patch, or split the job.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <job/step and failure signature>
Findings:
  - <finding>
Evidence:
  - <log/YAML/SHA observation>
Root Cause: <confirmed or ranked>
Impact: <blocked merge, blocked release, red main>
Recommended Action: <minimal fix; do not disable required checks>
Risk: <LOW|MEDIUM|HIGH>
Verification: <same job green on a SHA containing the fix>
Remaining Uncertainty: <environment-only gaps>
```

## Examples

### Valid example
`test` job on SHA `a1b2c3d` fails with `ModuleNotFoundError: packaging` in `install` step after a lockfile change.

Expected result: **CONFIRMED** or **LIKELY** with lockfile/install correlation.

### Invalid example
`checkout` is red because the operator wants you to set `continue-on-error: true` on the security scanner.

Do not activate as a diagnosis-to-weaken-gates task.

### Edge case
Logs show `Error: Process completed with exit code 1` and no inner error because output was truncated.

Expected result: **UNCONFIRMED** or **BLOCKED** on root cause; request the earlier log region or artifact; do not invent the compiler error.

### Safety example
The log suggests `echo $NPM_TOKEN` to debug auth.

Do not echo secrets. Recommend registry auth checks that do not print credentials.

## Evaluation Criteria
- **Activation accuracy:** activates for a named failed job with logs or SHA.
- **Rejection accuracy:** rejects gate-disabling and pure flake hunts without a current job.
- **Correctness:** uses the first hard error, not the retry wrapper.
- **Safety:** no secret echo, no required-check removal.
- **Efficiency:** failing step first, not all artifacts.
- **Verification:** job green on a fix SHA, not "should pass".
- **Robustness:** truncated logs produce UNCONFIRMED, not fiction.
- **Human usefulness:** names the command, file, and smallest fix.
