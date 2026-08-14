# Recover a Secret That Entered Git

Complements `recover-committed-secret`. This is the human incident checklist.

## Problem
A credential is in a tracked file, commit, or reachable history.

## Symptoms
Secret scanning alert, reviewer seeing a key in a diff, CI log echoing a token.

## Prerequisites
Ability to rotate the credential. Git access. Do not require the raw secret to be pasted into chat.

## Diagnosis
1. Classify: working tree / index / unpublished commit / pushed history.
2. Identify introducing path and commit with path-limited log.
3. Assume pushed if unknown.
4. Check whether a later commit merely deleted the line (blob may remain).

## Commands

```bash
git status -- <path>
git log --oneline -- <path>
git log -p -- <path>   # redact output; do not copy values into tickets
git ls-remote origin
```

History purge tools (`git filter-repo`) belong in a backup clone after rotation and approval. They are not first steps.

## Interpretation
- HEAD clean ≠ history clean
- Force-push ≠ all forks and CI caches updated
- Rotation is the actual containment

## Common Causes
`.env` committed, example file replaced with real values, CI echo of env, "temporary" key in a test fixture.

## Resolution
1. Rotate and revoke the credential.
2. Remove from the tree; add ignore/hooks.
3. If published history: coordinated purge + invalidate host caches.
4. Notify anyone who cloned the ref.

## Verification
Issuing system shows the old credential revoked. Scanner quiet. Blob reachability checked after purge — or explicitly left as residual risk.

## Prevention
Pre-commit secret scanning, `.gitignore` for env files, short-lived tokens, never ARG/ENV secrets in Docker layers.

## Related Skills
`recover-committed-secret`, `review-pull-request`
