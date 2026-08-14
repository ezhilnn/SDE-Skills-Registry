# Skill Catalog

Lookup by symptom. Activate only the matching skill. If two skills appear to match, prefer the more specific one and record the other as a non-activation.

| Skill | Category | Activate when | Do not activate when | Mode | Risk |
| --- | --- | --- | --- | --- | --- |
| [investigate-intermittent-http-500](debugging/investigate-intermittent-http-500/SKILL.md) | debugging | HTTP 5xx on a subset of requests, instances, versions, regions, or inputs | Consistent 100% 5xx, 4xx, build/deploy failure, or production remediation | advisory | medium |
| [recover-committed-secret](git/recover-committed-secret/SKILL.md) | git | A secret is in git history, a commit, or a tracked file | Secret exists only in an untracked local file and was never staged | assisted | high |
| [diagnose-failing-ci-job](ci-cd/diagnose-failing-ci-job/SKILL.md) | ci-cd | A specific CI job/step failed and logs or status are available | Local test failure with no CI artifact, or a request to disable required checks | advisory | medium |
| [diagnose-crashloopbackoff](kubernetes/diagnose-crashloopbackoff/SKILL.md) | kubernetes | A pod/workload is in CrashLoopBackOff or restarting until backoff | ImagePullBackOff, Pending unschedulable, or a request to delete/restart production pods | advisory | medium |
| [investigate-postgres-blocking](databases/investigate-postgres-blocking/SKILL.md) | databases | Queries wait behind locks; `waiting`/`blocked` sessions or lock timeouts | Slow queries with no lock evidence, or a request to `pg_terminate_backend` in production | advisory | high |
| [review-pull-request](code-quality/review-pull-request/SKILL.md) | code-quality | A bounded diff needs correctness, safety, and test review | Architecture redesign, incident response, or merge/deploy of the PR | advisory | medium |
| [investigate-flaky-test](testing/investigate-flaky-test/SKILL.md) | testing | The same test both passes and fails without an intentional code change | A test that always fails, or a request to quarantine by skipping in production CI without approval | advisory | medium |
| [diagnose-image-build-failure](docker/diagnose-image-build-failure/SKILL.md) | docker | `docker build` / CI image build exits non-zero | Runtime container crash after a successful build, or a request to publish an unsigned production image | advisory | medium |
