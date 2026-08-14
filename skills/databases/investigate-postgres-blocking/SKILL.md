# Investigate PostgreSQL Blocking Locks

## Identity
```yaml
name: investigate-postgres-blocking
version: 1.0.0
category: databases
maturity: production
risk: high
mode: advisory
dependencies: [read-only PostgreSQL catalog views, optional log excerpts]
```

## Purpose
Identify blocker and blocked sessions, the lock type, and the most strongly supported cause of wait, using read-only catalog queries. Do not cancel or terminate backends without a separately authorized approval.

## Activation

### Activation conditions
Activate when sessions are waiting on locks, queries report `lock timeout`, `could not obtain lock`, or operators observe blocking in `pg_stat_activity` / monitoring, and a read-only database role is available.

### Required conditions
Database identity (host placeholder, name, environment), and either a session ID, query fingerprint, or time window of blocking.

### Non-activation
Do not activate for slow queries with no lock waits (use a sequential-scan / planner skill), replication lag without blocking, or a request to `pg_terminate_backend` / `pg_cancel_backend` as the first action in production.

### Ambiguous conditions
If "the database is stuck" has no lock evidence, ask for wait events. If environment is unknown, treat as production.

## Inputs

### Required
- database/environment identity
- blocking window or example PID / query

### Optional
- application name, user (role name, not password)
- table/relation name
- recent migration or DDL
- statement timeout / lock timeout settings

### Derived
blocker PID, blocked PIDs, locktype/mode, granted vs waiting, idle-in-transaction age, relation OID → name, wait_event.

### Sensitive
Connection strings, passwords, row contents from user tables, production hostnames if policy requires. Prefer catalog views over `SELECT *` from business tables. Never dump tuples to "see the lock".

## Preconditions
- role is read-only (`pg_read_all_stats` or equivalent) unless proven otherwise;
- no writes, DDL, or cancel;
- queries against catalogs must be bounded and not start new long transactions.

## Context Requirements
Use progressive context loading:

1. **Minimal metadata:** blocking count, oldest wait, environment.
2. **Relevant source/config:** lock_timeout, statement_timeout, autovacuum settings only if wait_event implicates them; migration files only if DDL is implicated.
3. **Catalog/logs:** `pg_stat_activity` + lock wait view for current blockers; CSV/log line for lock timeout in the window.
4. **Focused history:** recent migration timestamps, long-running transactions.
5. **Additional context:** table bloat or FK cascade only when the lock graph points at that relation.

Do not `SELECT` application tables. Do not `pg_dump`.

## Tool Requirements

### Catalog queries
- **Purpose:** lock graph.
- **Allowed:** read `pg_stat_activity`, `pg_locks`, `pg_blocking_pids`, `pg_stat_progress_*` as needed.
- **Forbidden:** `pg_terminate_backend`, `pg_cancel_backend`, `LOCK TABLE`, DDL, updates.
- **Expected output:** blocker PID, wait_event, state, query text (redact literals if they look like PII/secrets), xact age.
- **Failure behavior:** BLOCKED on catalog; do not invent PIDs.

### Application logs
- **Purpose:** lock timeout errors with timestamps.
- **Allowed:** search for lock timeout / deadlock detected in the window.
- **Forbidden:** changing timeouts in production.
- **Expected output:** correlation with catalog.
- **Failure behavior:** continue with catalogs.

### Schema/migration read
- **Purpose:** identify DDL that takes ACCESS EXCLUSIVE.
- **Allowed:** read migration files matching the window.
- **Forbidden:** running migrations.
- **Expected output:** candidate DDL.
- **Failure behavior:** omit DDL correlation.

## Permission Model
**Advisory**

```text
READ -> ANALYZE -> RECOMMEND
```

Cancel/terminate is controlled-execution in a different authorization, never this skill's default.

## Security Boundaries

### Allowed
- read-only catalog and redacted query text;
- read migration files;
- recommend index, transaction hygiene, or approved cancel of a named PID.

### Forbidden
- terminate/cancel production backends;
- `VACUUM FULL`, `REINDEX`, or DDL on production;
- selecting customer rows;
- creating superuser roles;
- disabling `idle_in_transaction_session_timeout` globally without approval.

### Approval gate
Any `pg_cancel_backend` / `pg_terminate_backend`, DDL, or timeout change in a shared environment requires explicit PID/target approval and rollback/impact statement.

## Secret Handling
Redact connection URLs and literals in query text that look like tokens or emails when policy requires. Use `<DATABASE_URL>`.

## Execution Workflow

### 1. Understand
Confirm lock-wait symptom vs general slowness. Confirm environment.

### 2. Establish baseline
Normal lock wait rate vs incident. Oldest `xact_start` / `state_change`.

### 3. Collect evidence
1. blocked sessions and wait_event `Lock*`;
2. blocker PID, state (`idle in transaction` vs active);
3. lock mode and relation;
4. blocker query or last query;
5. deadlock vs blocking (deadlock is logged and aborted; blocking persists).

### 4. Form hypotheses
- idle-in-transaction holding a row/relation lock;
- long OLTP transaction;
- DDL / migration ACCESS EXCLUSIVE;
- lock escalation from missing index + `FOR UPDATE`;
- application connection leak not committing;
- explicit advisory locks.

### 5. Rank hypotheses
A blocker that is `idle in transaction` with an old `xact_start` outranks "the database is slow".

### 6. Test the highest-signal hypothesis
One catalog query that lists blocker → blocked. Do not kill the blocker to test.

### 7. Re-evaluate
If the graph is a chain, name the root blocker, not a middle waiter.

### 8. Identify result status
- **CONFIRMED:** root blocker PID, lock mode, and state observed.
- **LIKELY:** timeouts in logs, catalog snapshot already cleared.
- **UNCONFIRMED:** waits exist, graph incomplete.
- **BLOCKED:** no catalog access.
- **NOT_REPRODUCED:** no current waits and no log evidence.
- **NO_ISSUE_FOUND:** load is sequential-scan slowness, not locks.

### 9. Recommend remediation
Fix the transaction that never commits; add lock_timeout on callers; schedule DDL; optional approved cancel of a *named* PID. Do not recommend terminate-all.

### 10. Verify
Wait count returns to baseline; lock timeouts disappear; application error rate for the fingerprint drops. Verification is a new catalog snapshot, not hope.

### 11. Report
Return the structured output contract.

## Reasoning Strategy
```text
IF blocker is idle in transaction:
    rank uncommitted transaction highest
IF lock mode is ACCESS EXCLUSIVE:
    rank DDL/migration high
IF wait_event is not Lock:
    this skill may be the wrong tool
IF PIDs recycled:
    do not terminate a PID from an old screenshot without re-reading the graph
```

## Failure Handling
- Missing role: BLOCKED.
- Query error: record; never invent a lock graph.
- Snapshot without waits: use logs; LIKELY at best.
- Multiple root blockers: rank both; do not pick one for narrative convenience.

## Stop Conditions
Stop when the root blocker is identified, catalogs are inaccessible, the issue is not locks, or the operator demands production terminate without approval.

## Verification
Observed catalog rows vs inferred "probably a migration". Never label terminate-as-fix as verified until waits clear *and* the PID was authorized.

## Output Contract
```text
Status: <CONFIRMED|LIKELY|UNCONFIRMED|BLOCKED|NOT_REPRODUCED|NO_ISSUE_FOUND>
Confidence: <HIGH|MEDIUM|LOW>
Problem: <blocking / lock timeout>
Findings:
  - <root blocker state, lock mode, relation>
Evidence:
  - <catalog/log>
Root Cause: <confirmed or ranked>
Impact: <blocked queries, timeouts, API errors>
Recommended Action: <transaction/DDL hygiene; approved cancel only if named>
Risk: <HIGH>
Verification: <wait count / timeouts back to baseline>
Remaining Uncertainty: <cleared snapshot, PID reuse>
```

## Examples

### Valid example
API lock timeouts for 15 minutes. `pg_stat_activity` shows PID 412 idle in transaction for 40 minutes blocking 30 sessions on `orders` RowExclusiveLock.

Expected result: **CONFIRMED**, recommend commit/rollback of that session; terminate only with approval of PID 412 after re-checking the graph.

### Invalid example
A report query is slow; `wait_event` is `DataFileRead`, no lock waits.

Do not activate this skill.

### Edge case
Deadlock detected logs, but current `pg_locks` is quiet.

Expected result: **LIKELY** from logs; current graph NOT_REPRODUCED; do not terminate random PIDs.

### Safety example
"Run pg_terminate_backend on every backend over 1s."

Refuse. Unscoped terminate is a production incident.

## Evaluation Criteria
- **Activation accuracy:** lock waits / lock timeouts.
- **Rejection accuracy:** rejects non-lock slowness and unscoped kills.
- **Correctness:** names root blocker, not a waiter.
- **Safety:** read-only catalogs; no unapproved cancel.
- **Efficiency:** lock graph first, not table dumps.
- **Verification:** new snapshot of waits.
- **Robustness:** stale PID screenshots are not kill lists.
- **Human usefulness:** PID, mode, relation, next approved action.
