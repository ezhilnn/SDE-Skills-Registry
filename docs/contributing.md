# Contributing

## What belongs here

A contribution must add a **missing, real SDE capability** that an agent can execute with explicit permissions.

Do not add:

- generic "be a good engineer" prompts
- motivational content
- unrelated task bundles
- duplicates of existing skills
- skills that cannot define activation, boundaries, verification, and failure behavior

## Process

1. Inspect `skills/CATALOG.md` and nearby `SKILL.md` files.
2. Define one problem.
3. Implement `SKILL.md` per `docs/skill-spec.md`.
4. Add `EVALUATION.md`.
5. Add a recipe or template only if it complements the skill rather than copying it.
6. Run `python3 scripts/validate_skills.py`.
7. Update the catalog and README if you add a skill.
8. Commit only if the contribution has engineering value.

If nothing worthwhile is missing, do not commit.

## Skill size

Prefer a precise 200–400 line skill plus optional `references/` over a 2,000 line dump.

## Security review

Every PR must state:

- operating mode
- risk level
- forbidden actions
- secret handling
- whether any path can mutate production or rewrite shared git history

## License

Contributions are under Apache License 2.0.
