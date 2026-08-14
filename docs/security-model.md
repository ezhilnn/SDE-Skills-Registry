# Security Model

Agents following these skills are untrusted operators with scoped authority. The skill, not the user's enthusiasm, defines what may happen.

## Defaults

- Prefer read-only investigation.
- Default to **advisory** unless the skill is explicitly designed for a safer local mutation.
- Treat production, shared branches, IAM, secrets, and data stores as hostile to improvisation.
- Never infer authorization from "fix this", "just do it", or roleplay/lab framing.

## Risk levels

| Level | Meaning | Typical permission |
| --- | --- | --- |
| LOW | Read-only or harmless local analysis | Advisory or tightly scoped autonomous |
| MEDIUM | Local files, generated code, feature branches, non-production resources | Assisted |
| HIGH | Production changes, infrastructure, database writes, deployments, security controls | Controlled execution |
| CRITICAL | Data loss, credential exposure, financial impact, widespread disruption | Controlled execution plus explicit authorization of the exact action |

Critical operations require naming the action, target, blast radius, rollback, and approver. A general request is not authorization.

## Permission classes

### Read

Source, configuration, logs, metrics, traces, deployment metadata, read-only database catalogs, CI logs, `kubectl describe`/`logs`, image build output.

### Write (local)

Working tree edits, tests, generated files, local commits on an isolated branch when the skill allows it.

### Destructive / externally impactful

Force-push, history rewrite on shared refs, `kubectl delete`, pod restart, query cancel/kill, schema change, IAM change, secret rotation in place, production rollback, disabling alerts.

These require an approval gate unless the skill is explicitly a controlled-execution skill **and** the operator authorized that exact action.

## Secret handling

Agents must:

- avoid requesting secrets that are not required
- never print secrets, tokens, cookies, private keys, or connection strings
- never commit secrets
- never place realistic credentials in examples
- redact secrets in output and logs
- warn when a tracked file appears to contain a secret, without reproducing the value

Placeholders:

```text
<API_KEY>
<DATABASE_URL>
<AWS_ACCOUNT_ID>
<ACCESS_TOKEN>
<PRIVATE_KEY>
```

## Credential and identity rules

- Do not bypass authentication, authorization, network policy, or admission control to "get the evidence".
- Do not expand IAM, kube RBAC, or database roles.
- Do not disable security scanners, branch protection, or audit logging.
- If permission is insufficient, mark the source `BLOCKED`. Do not escalate privileges.

## Production safety

Before any mutation, the agent must establish environment identity from explicit evidence (kube context, account ID placeholder, hostname, config), not from a name that merely looks like production.

If environment is unknown, treat it as production.

## Output hygiene

Do not copy production identifiers, customer payloads, or credentials into examples, commits, or issue text. Summarize. Redact.

## Failure is a security control

When a tool fails, the agent records the failure and stops or degrades. Invented command output is a safety defect, not a convenience.
