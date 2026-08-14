# Authoring Guide

Write skills as if a competent on-call engineer will be judged by them.

## Choose the problem

One real SDE task. Narrow enough that activation can be yes/no.

Bad: "Debug Kubernetes."

Good: "Diagnose a pod stuck in CrashLoopBackOff."

Before writing:

1. Read `skills/CATALOG.md`.
2. Reject duplicates.
3. Name the decision the agent must make and the evidence that would settle it.

## Write identity first

Set `risk` and `mode` from the most dangerous action the workflow might take, not from the average action.

If the skill investigates with `kubectl logs` but the tempting next step is `kubectl delete pod`, the skill is still advisory unless it is explicitly a controlled-execution remediator.

## Activation is a classifier

Activation conditions are inclusion tests.

Non-activation conditions are exclusion tests and pointers to a better skill.

Ambiguous conditions require a question, not a guess.

Required conditions are the minimum facts without which execution is unsafe or meaningless.

## Inputs

Separate required, optional, derived, and sensitive inputs.

Do not ask for secrets "in case they help".

## Tools

For each tool, state purpose, allowed use, forbidden use, expected output, and failure behavior.

Do not assume a tool exists. Do not invent flags. Prefer the cheapest high-signal check.

## Workflow

Use explicit phases. A typical investigation:

1. Understand
2. Establish baseline
3. Collect evidence
4. Form hypotheses
5. Rank hypotheses
6. Test the highest-signal hypothesis
7. Re-evaluate
8. Identify root cause or ranked causes
9. Recommend or perform remediation within mode
10. Verify
11. Report

Do not jump from symptom to conclusion.

## Token discipline

- Keep `SKILL.md` executable, not encyclopedic.
- Move command catalogs to `references/` if they bloat the skill.
- Instruct targeted search, then summarize large outputs.
- Forbid whole-repo ingestion unless evidence requires a named expansion.

## Examples

Include all four:

- valid activation
- invalid activation
- edge case
- safety refusal or approval gate

## Evaluation

Ship `EVALUATION.md` with the skill. If safety or correctness fails, `maturity` stays `draft` or `experimental`.

## Voice

Imperative, specific, bounded. No motivational language. No hidden chain-of-thought requirements. Final user-facing output is structured evidence, not a memoir of the search.
