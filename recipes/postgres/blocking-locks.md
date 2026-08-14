# PostgreSQL Blocking Locks

Complements `investigate-postgres-blocking`.

## Problem
Sessions wait on locks; clients see lock timeouts or stalls.

## Symptoms
`canceling statement due to lock timeout`, blocked queries in dashboards, idle-in-transaction growth.

## Prerequisites
Read-only catalog role. Environment identity. Do not start with terminate.

## Diagnosis
1. Confirm wait_event is lock-related.
2. Build blocker → blocked graph.
3. Inspect the *root* blocker's state and `xact_start`.
4. Distinguish idle-in-transaction, long DML, and ACCESS EXCLUSIVE DDL.

## Commands

```sql
-- Read-only illustration; privilege names vary by version/role
SELECT pid, state, wait_event_type, wait_event, xact_start, query
FROM pg_stat_activity
WHERE wait_event_type = 'Lock' OR state = 'idle in transaction';
```

Re-read the graph immediately before any approved cancel. PIDs are reused.

## Interpretation
Idle-in-transaction with an old transaction start is the usual root. Killing waiters does not release the lock.

## Common Causes
Application never commits, forgotten admin session, migration, `FOR UPDATE` over a large set, advisory locks.

## Resolution
Fix the transaction. Optionally cancel a *named* PID after approval. Do not terminate all backends.

## Verification
Fresh snapshot: wait count at baseline; application lock-timeout errors gone.

## Prevention
`idle_in_transaction_session_timeout`, short transactions, lock_timeout on OLTP roles, DDL windows.

## Related Skills
`investigate-postgres-blocking`
