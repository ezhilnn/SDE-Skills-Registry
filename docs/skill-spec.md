# Skill Specification

This document is the production contract for agent-executable skills.

A skill is a bounded procedure. It is not a persona, a checklist of slogans, or a dump of tribal knowledge.

## Required identity fields

```yaml
name: <kebab-case unique name>
version: <semver>
category: <debugging|git|ci-cd|databases|docker|kubernetes|cloud|code-quality|reliability|observability|security|testing|release-engineering>
maturity: <draft|experimental|production>
risk: <low|medium|high|critical>
mode: <advisory|assisted|controlled-execution|autonomous>
dependencies: [<evidence sources or tools the skill needs>]
```

`maturity: production` is allowed only after evaluation in `EVALUATION.md` passes safety and correctness.

## Required sections

Every `SKILL.md` must contain these headings, in this order:

1. Identity
2. Purpose
3. Activation
4. Non-Activation
5. Inputs
6. Preconditions
7. Context Requirements
8. Tool Requirements
9. Permission Model
10. Security Boundaries
11. Execution Workflow
12. Reasoning Strategy
13. Failure Handling
14. Stop Conditions
15. Verification
16. Output Contract
17. Examples
18. Evaluation Criteria

`Activation` must include activation conditions, required conditions, and ambiguous conditions. `Non-Activation` may be a sibling heading or a subsection; validators accept either.

## Operating modes

| Mode | Sequence | Default use |
| --- | --- | --- |
| Advisory | READ → ANALYZE → RECOMMEND | Investigation, review, diagnosis |
| Assisted | READ → ANALYZE → PREPARE → REQUEST APPROVAL | Local mutations, history rewrite plans, kill-query plans |
| Controlled execution | READ → ANALYZE → PLAN → APPROVAL → EXECUTE → VERIFY | Authorized changes with explicit approval |
| Autonomous | DETECT → ANALYZE → EXECUTE → VERIFY | Only genuinely low-risk local actions |

Do not infer a more powerful mode from a user's informal wording.

## Evidence language

The agent must label claims as:

- **observation** — retrieved from a tool or artifact
- **hypothesis** — candidate explanation
- **evidence** — observation that supports or contradicts a hypothesis
- **conclusion** — status-labeled result
- **uncertainty** — what remains unproven

Correlation is not confirmation. Missing data is `Unknown`, `Not verified`, `Insufficient evidence`, `Tool unavailable`, or `Requires human investigation`.

## Context loading

Load context in stages. Expand only when a ranked hypothesis cannot be tested with current evidence.

Do not instruct the agent to ingest an entire repository, complete log history, or unrelated services.

## Output contract

Production skills must emit:

```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem:
Findings:
Evidence:
Root Cause:
Impact:
Recommended Action:
Risk:
Verification:
Remaining Uncertainty:
```

Never label an inferred result as verified.

## File layout

```text
skills/<category>/<skill-name>/SKILL.md
skills/<category>/<skill-name>/EVALUATION.md
```

Optional: `references/` for large command catalogs that would otherwise bloat the skill.

## Rejection rules

Do not publish a skill if:

- activation is vague
- permissions or forbidden actions are missing
- verification is missing
- it duplicates an existing skill
- it combines unrelated tasks
- it cannot be evaluated
- an experienced SDE would not use the procedure
