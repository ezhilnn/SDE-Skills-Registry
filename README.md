# SDE Agent Skills

Reusable, executable workflows that teach AI agents **how to perform software engineering work safely**, not what answer to invent.

This repository is engineering infrastructure for agents: activation conditions, permission models, evidence rules, stop conditions, and verification contracts.

It is not a prompt pack.

## Layers

Do not mix these concepts.

| Layer | Audience | Purpose |
| --- | --- | --- |
| **Skills** | Agents | Deterministic, permissioned workflows for one engineering task |
| **Recipes** | Humans | Diagnosis and resolution procedures that complement skills |
| **Templates** | Humans and agents | Reusable implementation patterns with failure and security constraints |

## Catalog

See [`skills/CATALOG.md`](skills/CATALOG.md) for activation-oriented lookup.

Current production skills:

- [`investigate-intermittent-http-500`](skills/debugging/investigate-intermittent-http-500/SKILL.md)
- [`recover-committed-secret`](skills/git/recover-committed-secret/SKILL.md)
- [`diagnose-failing-ci-job`](skills/ci-cd/diagnose-failing-ci-job/SKILL.md)
- [`diagnose-crashloopbackoff`](skills/kubernetes/diagnose-crashloopbackoff/SKILL.md)
- [`investigate-postgres-blocking`](skills/databases/investigate-postgres-blocking/SKILL.md)
- [`review-pull-request`](skills/code-quality/review-pull-request/SKILL.md)
- [`investigate-flaky-test`](skills/testing/investigate-flaky-test/SKILL.md)
- [`diagnose-image-build-failure`](skills/docker/diagnose-image-build-failure/SKILL.md)

## Design contract

Every production skill must implement the sections in [`docs/skill-spec.md`](docs/skill-spec.md).

Non-negotiable properties:

- one problem, one skill, one workflow
- evidence distinguished from inference
- explicit allow/forbid/approval gates
- progressive context loading
- stop conditions and verification criteria
- structured output with confidence and remaining uncertainty

## Security

Default operating mode is the safest applicable mode. Autonomous production mutation is not a default.

Read [`docs/security-model.md`](docs/security-model.md) before authoring or executing a skill.

## Quality bar

A skill is production-ready only if an experienced engineer would trust the procedure on a real incident or change, and if it passes [`docs/evaluation.md`](docs/evaluation.md).

Validate locally:

```bash
python3 scripts/validate_skills.py
```

## Contributing

See [`docs/contributing.md`](docs/contributing.md) and [`docs/authoring-guide.md`](docs/authoring-guide.md).

Prefer one excellent skill over a bundle of vague ones. If a contribution does not add a missing capability, do not add it.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
