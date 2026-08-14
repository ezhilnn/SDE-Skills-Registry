# Diagnose a Container Image Build Failure

## Identity
```yaml
name: diagnose-image-build-failure
version: 1.0.0
category: docker
maturity: production
risk: medium
mode: advisory
dependencies: [Dockerfile, build log, build context metadata]
```

## Purpose
Locate the failing build stage/instruction and the most strongly supported cause of a non-zero `docker`/`buildah`/`buildx` build. Do not publish an image or disable image scanning to get a green build.

## Activation

### Activation conditions
Activate when an image build exits non-zero, and a Dockerfile (or equivalent) plus build log or failing instruction are available.

### Required conditions
Dockerfile path or inline content, and the failing log region or step number.

### Non-activation
Do not activate for a container that crashes after a successful build (`diagnose-crashloopbackoff` or runtime debug), for CI wrapper failures before `docker build` runs (`diagnose-failing-ci-job`), or for a request to push an unsigned image to production.

### Ambiguous conditions
If both `docker build` and a later `docker run` fail, ask which log is in scope. If multiple Dockerfiles exist, ask which one.

## Inputs

### Required
- Dockerfile identity
- build log or failing instruction

### Optional
- build-args (names, not secret values)
- base image digest/tag
- `.dockerignore`
- platform (`linux/amd64` vs `arm64`)
- build tool (buildx, kaniko, buildah)

### Derived
Failing stage, instruction, exit code, network vs compile vs copy-path, cache hit up to step N.

### Sensitive
Build-args that are secrets, `COPY` of `.env`, registry credentials in logs. Never add `ARG` secrets that persist in layers. Use BuildKit secret mounts as a recommendation, not `ENV PASSWORD=`.

## Preconditions
- diagnosis is read-only plus optional local rebuild without push;
- no `--push` to production registries;
- do not use `--no-cache` first unless cache corruption is the hypothesis.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** tool, platform, failing step, base image.
2. **Relevant source/config:** Dockerfile from the start through the failing instruction, plus `.dockerignore` if COPY failed.
3. **Logs:** failing instruction output, not the entire successful cache replay if long.
4. **Focused history:** Dockerfile diff vs last green image.
5. **Additional context:** package lockfiles or the copied source file only if that instruction failed.

Do not send the entire build context listing unless COPY context is implicated.

## Tool Requirements

### docker build / buildx
- **Purpose:** confirm the failing instruction.
- **Allowed:** rebuild locally without `--push`; `--progress=plain`; target the failing stage.
- **Forbidden:** `--push` to shared/production registries; `--network=host` unless required and approved; building with production secrets in ARG.
- **Expected output:** same failure or divergence.
- **Failure behavior:** use the provided log; mark local rebuild not achieved.

### Dockerfile read
- **Purpose:** interpret the instruction.
- **Allowed:** read Dockerfile, ignore file, related scripts `RUN`ed.
- **Forbidden:** rewriting to `curl | bash` as a "fix".
- **Expected output:** candidate cause.
- **Failure behavior:** BLOCKED if Dockerfile missing.

### registry/base pull errors
- **Purpose:** distinguish FROM failure from RUN failure.
- **Allowed:** read error codes (401/403/manifest unknown).
- **Forbidden:** embedding registry passwords in the Dockerfile.
- **Expected output:** auth vs missing tag vs platform.
- **Failure behavior:** UNCONFIRMED on FROM.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

## Security Boundaries

### Allowed
- read Dockerfile and logs;
- local rebuild without push;
- recommend pin digests, `.dockerignore`, BuildKit secrets.

### Forbidden
- pushing to production;
- disabling image vulnerability gates;
- storing secrets in layers (`ENV`/`ARG` leaked);
- `--privileged` build as a casual fix;
- fetching unsigned scripts over HTTP as the recommended install.

### Approval gate
Registry credential changes, base-image upgrades in production pipelines, and push rights require explicit approval.

## Secret Handling
If the log prints a token, report exposure and rotate. Recommend `--secret` / mount, never `ARG TOKEN` that remains in history.

## Execution Workflow

### 1. Understand
Tool, Dockerfile, whether failure is FROM, COPY, RUN, or export.

### 2. Establish baseline
Last green Dockerfile SHA / image tag.

### 3. Collect evidence
1. last instruction before error;
2. exit code and compiler/package manager message;
3. COPY paths vs `.dockerignore`;
4. platform mismatch;
5. network/registry 401.

### 4. Form hypotheses
- missing file in context;
- package version/lock drift;
- base image tag moved;
- platform (exec format / qemu);
- secret/registry auth;
- OOM during compile;
- syntax/heredoc error.

### 5. Rank hypotheses
Match the instruction type. A COPY error is not a compiler bug.

### 6. Test the highest-signal hypothesis
One local rebuild of the failing stage, or inspect context for the COPY path.

### 7. Re-evaluate
Cache can hide earlier failures; if the log starts at a late RUN, still confirm FROM succeeded.

### 8. Identify result status
- **CONFIRMED:** instruction + error + file/cause.
- **LIKELY:** log match, no local rebuild.
- **UNCONFIRMED:** generic `executor failed running`.
- **BLOCKED:** no Dockerfile/log.
- **NOT_REPRODUCED:** local build succeeds.
- **NO_ISSUE_FOUND:** build succeeded; operator misread a warning.

### 9. Recommend remediation
Pin, fix COPY, fix package install, use secrets mounts. Do not recommend `--push --force` or skipping scan.

### 10. Verify
Clean rebuild of the same Dockerfile/platform exits 0. Push is a separate authorized step.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
```text
IF COPY fails:
    rank context/dockerignore/path
IF FROM fails:
    rank tag/auth/platform
IF RUN compile OOM:
    rank builder memory, not application runtime
IF local pass and CI fail:
    rank platform, build-arg, and context differences
```

## Failure Handling
- Truncated CI log: request `--progress=plain` region.
- Cannot run Docker: diagnose from Dockerfile+log only.
- Conflicting: BuildKit vs legacy builder differences stated as uncertainty.

## Stop Conditions
Stop when the instruction is explained, logs/Dockerfile missing, or the operator demands a production push.

## Verification
Exit code 0 on a rebuild is verified. "Should work on the registry" is not.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <image build failure>
Findings:
  - <stage, instruction, error>
Evidence:
  - <log/Dockerfile>
Root Cause: <confirmed or ranked>
Impact: <blocked image, blocked deploy>
Recommended Action: <minimal Dockerfile/context fix; no unapproved push>
Risk: <MEDIUM>
Verification: <rebuild exit 0 on same platform>
Remaining Uncertainty: <CI-only context, truncated logs>
```

## Examples

### Valid example
Build fails at `COPY app/package-lock.json` — file is listed in `.dockerignore`.

Expected result: **CONFIRMED**.

### Invalid example
Image built successfully; the container exits 137 at runtime.

Do not activate this skill.

### Edge case
`executor failed running [/bin/sh -c npm ci]: exit 1` with npm log truncated.

Expected result: **UNCONFIRMED** until the npm error is obtained; do not invent a missing module name.

### Safety example
"Put NPM_TOKEN in an ARG so the build works, then push to prod."

Refuse persisting secrets in layers and unapproved production push. Recommend BuildKit secret mounts and a non-production registry first.

## Evaluation Criteria
- **Activation accuracy:** failed image build.
- **Rejection accuracy:** runtime crashes and pre-build CI.
- **Correctness:** maps instruction type to cause class.
- **Safety:** no secret layers, no unapproved push.
- **Efficiency:** failing instruction first.
- **Verification:** rebuild exit 0.
- **Robustness:** truncated logs stay UNCONFIRMED.
- **Human usefulness:** exact instruction and smallest fix.
