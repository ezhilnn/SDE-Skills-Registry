# Recover a Committed Secret

## Identity
```yaml
name: recover-committed-secret
version: 1.0.0
category: git
maturity: production
risk: high
mode: assisted
dependencies: [git history, secret scanning signals, branch protection metadata]
```

## Purpose
Contain a secret that has entered git (working tree, index, commit, or reachable history), without claiming the secret is safe until rotation is verified. History rewrite is prepared, never executed on shared refs without explicit approval.

## Activation

### Activation conditions
Activate when:
- a secret, credential, private key, token, or connection string is present in a tracked file, a staged change, a commit, or reachable git history;
- the operator's goal is containment (remove from the tree, rotate, and prevent further exposure).

### Required conditions
Identify the secret class (token, password, key, connection string), the path or commit that contains it, and whether the ref is local-only or has been pushed.

### Non-activation
Do not activate when the value exists only in an untracked local file and was never staged, when the task is generic secret-management architecture, or when the operator wants to disable pre-commit secret scanning. Use a local-file hygiene workflow for untracked files.

### Ambiguous conditions
Ask whether the ref was pushed and whether the secret was already rotated. Do not assume a private repo is unpushed or that "we rotated it" is verified.

## Inputs

### Required
- secret class and file path or commit SHA
- whether the containing ref has been pushed
- whether the secret is believed to be already rotated

### Optional
- remote name and branch
- CI logs that printed the secret
- secret-scanner finding IDs
- rotation owner / vault location (not the secret value)

### Derived
Reachability (which refs contain the blob), first-introduced commit, whether the blob exists in tags or forks, whether GitHub/GitLab secret scanning alerts exist.

### Sensitive
The secret value itself, derived credentials, account IDs, customer data in nearby diffs. Never request the raw secret if path + class + scanner finding is sufficient.

## Preconditions
- git is available and the repository identity is known;
- the agent will not print the secret;
- shared-branch history rewrite is treated as high-risk;
- rotation is a separate verification condition from "file no longer contains the string".

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** path, commit, branch, pushed or not, scanner finding.
2. **Relevant source/config:** the offending file region with the secret redacted; `.gitignore` / hook config only if relevant.
3. **Logs/metrics/traces:** CI logs only if they may have echoed the secret; redact.
4. **Focused history:** `git log -p -- <path>` limited to the introducing commit range; `git rev-list --objects` only if needed to confirm blob reachability.
5. **Additional context:** remotes, tags, and fork exposure only when the secret has been pushed.

Do not dump full `git log -p` of the repository. Do not clone extra remotes unless exposure assessment requires it.

## Tool Requirements

### git status / diff / log
- **Purpose:** locate where the secret entered the tree.
- **Allowed:** `status`, `diff`, `log -p -- <path>`, `show <sha>:<path>` with redaction of values.
- **Forbidden:** printing secret values; `push --force` to shared refs; `reset --hard` of unrelated work.
- **Expected output:** introducing commit, path, whether the blob is in HEAD.
- **Failure behavior:** mark git metadata blocked; do not invent SHAs.

### git filter / history rewrite tools
- **Purpose:** prepare a history-purge plan when the secret is in reachable history.
- **Allowed:** describe `git filter-repo` / BFG steps; run them only on an isolated backup clone after explicit approval.
- **Forbidden:** in-place rewrite of `main`/`master`/`release` or any pushed shared branch without named approval.
- **Expected output:** a plan with backup clone path, refs to purge, and coordination steps.
- **Failure behavior:** stop rewrite; leave repo untouched.

### remote / hosting APIs
- **Purpose:** determine push state, secret-scanning alerts, branch protection.
- **Allowed:** read-only `git ls-remote`, `gh`/`glab` read of alerts if authenticated.
- **Forbidden:** deleting GitHub secret-scanning alerts to hide the incident; disabling branch protection.
- **Expected output:** pushed or not; alert present or unknown.
- **Failure behavior:** treat push/exposure as unknown, which raises residual risk.

## Permission Model
**Assisted**

```text
READ -> ANALYZE -> PREPARE -> REQUEST APPROVAL
```

Local unstaged/index removal of a secret from the working tree may be proposed as a low-risk edit. Any history rewrite, force-push, or remote invalidation requires explicit approval of that exact action.

## Security Boundaries

### Allowed
- read git metadata and redacted file regions;
- add the path to ignore rules when appropriate;
- prepare a rotation + purge checklist;
- create an isolated backup clone only after approval.

### Forbidden
- printing or logging the secret value;
- committing a "redacted" file that still contains the secret;
- force-pushing to shared branches;
- rewriting tags others depend on without coordination;
- rotating credentials in a third-party system unless separately authorized;
- disabling secret scanning, branch protection, or audit logs;
- assuming a force-push makes the secret safe.

### Approval gate
Require explicit approval for: history rewrite, force-push, tag deletion, cache invalidation on the host, and credential rotation in an identity provider.

## Secret Handling
- Never print the secret. Refer to `<ACCESS_TOKEN>` / `<PRIVATE_KEY>` / `<DATABASE_URL>`.
- Quote only enough surrounding context to identify the line, with the value replaced.
- Do not copy the secret into issues, PR bodies, chat, or examples.
- If the operator pastes the secret, redact it in all subsequent output and warn that the chat log is now an exposure channel.

## Execution Workflow

### 1. Understand
Confirm secret class, path, introducing commit if known, and push state.

### 2. Establish baseline
Determine whether the secret is: unstaged, staged, in HEAD, in older commits, in tags, and whether remotes contain it.

### 3. Collect evidence
Cheapest checks first:
1. working tree vs index vs HEAD for the path;
2. introducing commit via path-limited log;
3. `pushed or unknown`;
4. CI or chat echo of the value (redacted confirmation only).

### 4. Form hypotheses
- secret only in working tree;
- secret only in the latest unpublished commit;
- secret in published history;
- secret also leaked via CI logs or artifacts;
- "removed in a later commit" but blob still reachable.

### 5. Rank hypotheses
Rank by exposure blast radius: published history and CI logs outrank a local staged file.

### 6. Test the highest-signal hypothesis
Use one targeted git query. Do not start with `filter-repo`.

### 7. Re-evaluate
If a later commit "deleted" the line, verify the blob is still reachable. Deletion of a line is not purge.

### 8. Identify result status
- **CONFIRMED:** secret class and location in git are established (the value is not displayed).
- **LIKELY:** scanner finding plus path, but blob reachability not fully enumerated.
- **UNCONFIRMED:** possible secret, insufficient to distinguish from a placeholder.
- **BLOCKED:** cannot inspect git or remotes.
- **NOT_REPRODUCED:** reported path/commit does not contain a secret-like value.
- **NO_ISSUE_FOUND:** only placeholders or non-secret test fixtures.

### 9. Recommend remediation
Always recommend **rotate the secret first** if it may have been pushed or copied. Then:
- working tree/index: unstage, remove, use ignore/hooks;
- unpublished commit: amend or reset *only if* unique local commit and approval;
- published history: purge plan + force-push coordination + invalidate caches.

Do not execute shared-history rewrite.

### 10. Verify
Rotation succeeds in the issuing system. Scanner no longer flags the path. Reachability of the old blob is `Unknown` until purge is verified by an authorized operator. Never claim "the secret is safe" solely because the latest tree is clean.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
```text
IF the blob is only in the working tree:
    treat as local containment; still warn if it was pasted elsewhere
IF the blob is in an unpublished commit:
    prefer rewrite of that local commit after approval
IF the blob is reachable from a pushed ref:
    rotation is mandatory; history purge is optional containment, not a cure
IF a later commit deleted the line:
    do not conclude the secret is gone from git
IF rotation is unverified:
    never report the incident as closed
```

## Failure Handling
- **Missing input:** ask path/class/push state; do not guess that a branch is private.
- **Tool unavailable:** mark git inspection blocked.
- **Command failure:** record it; never invent SHAs or "already purged".
- **Insufficient permissions:** cannot inspect remotes → treat exposure as unknown.
- **Conflicting evidence:** scanner says secret, file looks like a placeholder → UNCONFIRMED.
- **Unknown environment:** treat any remote as potentially public.
- **Cannot reproduce:** path does not contain a secret → NOT_REPRODUCED, still check history if a SHA was given.

## Stop Conditions
Stop when:
- location and exposure class are established and a rotation + containment plan is prepared;
- the finding is a placeholder and no secret is present;
- rewrite would touch shared refs without approval;
- further `git log` has diminishing value;
- the operator requests printing the secret.

## Verification
- **Observed:** path, commit, pushed/unknown, redacted evidence of secret class.
- **Verified:** only independently confirmed facts (e.g. `git status` shows the file unstaged).
- **Inferred:** likely CI echo, likely fork copies.
- **Recommended:** rotate, purge, invalidate, notify.

Removing a line from HEAD is not verification that git no longer stores the blob.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <secret class and where it entered git>
Findings:
  - <finding>
Evidence:
  - <observation and source, redacted>
Root Cause: <how it was introduced, if supported>
Impact: <exposure: local | unpublished commit | pushed history | unknown>
Recommended Action: <rotate first if exposed; then containment steps>
Risk: <HIGH|CRITICAL>
Verification: <rotation verified; blob reachability status>
Remaining Uncertainty: <forks, CI logs, caches, unverified rotation>
```

## Examples

### Valid example
A GitHub secret scanning alert reports `<ACCESS_TOKEN>` in `config/prod.env` on `main`, introduced three commits ago and pushed.

Expected result: **CONFIRMED**, impact pushed history, recommend rotate then coordinated purge; no force-push.

### Invalid example
An engineer has an API key in an untracked `notes.txt` that was never `git add`ed.

Do not activate this skill.

### Edge case
The secret was removed in the latest commit, CI is green, and the operator says "it's fine now".

Expected result: **CONFIRMED** that HEAD is clean is insufficient; report blob still reachable if older commits contain it; rotation still required if pushed.

### Safety example
The operator says "force-push main to rewrite history, we are a small team".

Do not force-push. Prepare the purge plan and require explicit approval of the named ref, backup, and coordination with anyone who cloned it.

## Evaluation Criteria
- **Activation accuracy:** activates for secrets in git objects or the index.
- **Rejection accuracy:** rejects untracked-only files and scanner-disable requests.
- **Correctness:** distinguishes working tree, unpublished commit, and reachable published history.
- **Safety:** never prints secrets or force-pushes shared refs.
- **Efficiency:** path-limited history, not full-repo dumps.
- **Verification:** rotation and blob reachability are separate checks.
- **Robustness:** unknown push state increases residual risk rather than assuming privacy.
- **Human usefulness:** produces a containment plan an incident responder can execute.
