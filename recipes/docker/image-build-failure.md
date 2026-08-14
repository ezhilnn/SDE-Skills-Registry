# Image Build Failure

Complements `diagnose-image-build-failure`.

## Problem
`docker build` / BuildKit / Kaniko exits non-zero.

## Symptoms
CI image job red, failing `COPY`/`RUN`/`FROM`.

## Prerequisites
Dockerfile and the failing log region.

## Diagnosis
1. Identify the instruction, not just the last helper line.
2. COPY → context and `.dockerignore`.
3. FROM → tag, auth, platform.
4. RUN → compiler, package manager, OOM, network.

## Commands

```bash
docker build --progress=plain -t local-debug:tmp .
# do not --push
```

## Interpretation
A successful local build and a failing CI build usually differ in platform, context, or build-args — not "Docker is broken".

## Common Causes
Ignored files, moved tags, lockfile drift, ARM vs AMD64, secrets in ARG, builder memory.

## Resolution
Fix the instruction and context. Use BuildKit secret mounts. Do not persist tokens in layers.

## Verification
Rebuild exit 0 on the same platform. Push is separate.

## Prevention
Pin base digests, keep `.dockerignore` reviewed, no secrets in Dockerfile.

## Related Skills
`diagnose-image-build-failure`, `diagnose-failing-ci-job`
