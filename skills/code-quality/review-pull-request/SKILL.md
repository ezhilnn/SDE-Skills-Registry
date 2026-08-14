# Review a Pull Request

## Identity
```yaml
name: review-pull-request
version: 1.0.0
category: code-quality
maturity: production
risk: medium
mode: advisory
dependencies: [bounded diff, test/CI status, repository conventions]
```

## Purpose
Produce an evidence-based review of a bounded diff: correctness, regressions, tests, and security-relevant issues. Do not merge, deploy, or expand the review into an unrelated rewrite.

## Activation

### Activation conditions
Activate when the operator asks for review of a pull request, merge request, or named branch diff, and the change set is available.

### Required conditions
Diff identity (PR URL, branch pair, or patch) and the intended merge base.

### Non-activation
Do not activate for live incident diagnosis, secret containment (`recover-committed-secret` if a secret is in the diff — hand off), or a request to merge/approve in the host without human approval. Do not activate for "review the whole codebase".

### Ambiguous conditions
If the diff is larger than a stated review budget (for example >1000 lines across unrelated systems), ask to split or name the priority paths. If the PR mixes generated lockfile noise with logic, ask which files are in scope.

## Inputs

### Required
- diff (PR, patch, or branch comparison)
- target branch

### Optional
- test results / CI status
- linked issue
- risk notes from the author
- repo test commands

### Derived
Changed paths, complexity hotspots, missing tests for changed behavior, secret-like strings, dangerous APIs (eval, pickle, shell=True, IAM wildcards).

### Sensitive
Secrets in the diff, customer data in fixtures, production URLs with credentials. Do not repeat secret values. Switch to `recover-committed-secret` if a live secret is present.

## Preconditions
- review is read-only against git and CI;
- comments are recommendations;
- the agent will not rubber-stamp without reading the diff.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** title, files changed, stats, CI status.
2. **Relevant source:** the diff hunks; surrounding functions only when a hunk is incomplete.
3. **Logs/CI:** failing checks related to this PR, not unrelated red main jobs unless they block interpretation.
4. **Focused history:** prior commits on the same PR if later commits fix earlier ones; blame only for the touched lines when needed.
5. **Additional context:** call sites of a changed function only when correctness cannot be judged from the hunk.

Do not read the entire repository "for architecture context" by default.

## Tool Requirements

### git diff / gh pr diff
- **Purpose:** obtain the change set.
- **Allowed:** diff against the merge base; file-limited reads.
- **Forbidden:** merging, force-pushing the author's branch, amending their commits.
- **Expected output:** hunks and stats.
- **Failure behavior:** BLOCKED.

### tests / linters
- **Purpose:** verify claimed behavior.
- **Allowed:** run existing test commands for affected packages.
- **Forbidden:** deleting tests to make CI green; reducing lint to silence the PR.
- **Expected output:** pass/fail for scoped tests.
- **Failure behavior:** mark tests unverified.

### secret scan of the diff
- **Purpose:** catch credentials.
- **Allowed:** pattern scan of added lines.
- **Forbidden:** posting the secret in a review comment.
- **Expected output:** path + secret class.
- **Failure behavior:** continue other review axes.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

## Security Boundaries

### Allowed
- read diff, tests, CI summaries;
- request changes;
- recommend tests.

### Forbidden
- merging the PR;
- approving with a host "approve" when policy requires a human;
- introducing backdoors or disabling auth "temporarily";
- committing secrets "for the reviewer's convenience";
- rewriting unrelated modules.

### Approval gate
Any push to the author's branch or merge is outside this skill.

## Secret Handling
If added lines contain credentials, do not approve. Report path and class only. Recommend rotation.

## Execution Workflow

### 1. Understand
Intent of the PR, scope, and non-goals from the description. If the description is empty, infer only from the diff and label intent as inferred.

### 2. Establish baseline
Merge base, CI status, size, generated vs authored files.

### 3. Collect evidence
1. authored logical changes;
2. tests added/updated matching behavior;
3. error handling and authz on new endpoints;
4. concurrency, retries, idempotency if relevant;
5. secret/PII in added lines.

### 4. Form hypotheses
- correct and well-tested;
- behavior change without tests;
- regression in error path;
- security defect (injection, authz bypass, secret);
- incomplete migration / feature flag.

### 5. Rank findings
Blockers: secrets, authz bypass, data loss, broken build.
Then correctness bugs.
Then missing tests.
Then nits, clearly labeled as nits.

### 6. Test the highest-signal hypothesis
Run the smallest relevant test or reason from a complete hunk plus callee.

### 7. Re-evaluate
Withdraw a finding if later hunks or tests contradict it.

### 8. Identify result status
- **CONFIRMED:** defects with file/line evidence.
- **LIKELY:** suspected race/authz without a failing test.
- **UNCONFIRMED:** cannot understand the change without missing context.
- **BLOCKED:** diff unavailable.
- **NOT_REPRODUCED:** claimed bug not in this diff.
- **NO_ISSUE_FOUND:** no blockers; residual nits optional.

### 9. Recommend remediation
Concrete, local fixes. Do not demand an architecture rewrite unless the diff itself introduces an unsafe pattern.

### 10. Verify
Re-review an updated diff; run tests if they exist. Do not claim "LGTM" until blockers are addressed or explicitly accepted by the human owner.

### 11. Report
Return the structured output contract, plus a severity-ordered finding list.

## Reasoning Strategy
```text
IF a secret is in added lines:
    blocker; do not continue as a style review only
IF behavior changes and tests do not:
    record missing coverage; do not invent that tests exist
IF comment is taste:
    label nit; do not block
IF CI is red for this SHA:
    do not claim the change is verified
```

## Failure Handling
- Huge unrelated diff: ask to split; review only named paths if the operator insists.
- Generated files: skip noise unless the generator config is wrong.
- Missing tests command: mark verification unverified.

## Stop Conditions
Stop when blockers and material findings are reported, the diff is inaccessible, or the operator asks to merge.

## Verification
Observed hunks vs verified tests. "Looks fine" is not verified.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <PR identity and review goal>
Findings:
  - <severity: blocker|bug|missing-test|nit> <file> <evidence>
Evidence:
  - <hunk/CI/test>
Root Cause: <if defects share a cause>
Impact: <merge risk>
Recommended Action: <request changes or human approve>
Risk: <LOW|MEDIUM|HIGH|CRITICAL>
Verification: <tests/CI on the SHA>
Remaining Uncertainty: <unrun tests, unread call sites>
```

## Examples

### Valid example
PR adds an HTTP handler and a test. Authz check is missing on the write path.

Expected result: **CONFIRMED** blocker/bug with file evidence; do not merge.

### Invalid example
"Review the entire monorepo for quality."

Do not activate.

### Edge case
PR is 8,000 lines of generated protobuf plus a 20-line handler change.

Expected result: review the handler and generator config; do not line-read generated stubs unless they are hand-edited.

### Safety example
PR adds `AWS_SECRET_ACCESS_KEY: <value>` to CI YAML.

Blocker. Do not reprint the value. Do not approve. Point to `recover-committed-secret`.

## Evaluation Criteria
- **Activation accuracy:** bounded PR/diff review.
- **Rejection accuracy:** rejects whole-repo reviews and merge-as-review.
- **Correctness:** findings tied to hunks; nits labeled.
- **Safety:** no merge, no secret reprint.
- **Efficiency:** diff-first, not repo-wide.
- **Verification:** CI/tests separated from opinion.
- **Robustness:** huge generated diffs are scoped.
- **Human usefulness:** severity-ordered, actionable comments.
