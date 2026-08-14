# Idempotent Mutation (HTTP)

## Intent
Make a client-safe retry of a creating or updating operation without duplicate side effects.

## When to use
POST that creates an order, payment capture, or any side effect the client may retry after a timeout.

## Pattern
- Client sends `Idempotency-Key` (or equivalent) unique per logical intent
- Server stores key → request hash → response for a bounded TTL
- Same key + same body: replay stored response
- Same key + different body: 409 Conflict
- Different key: new intent

## Constraints
- Storage of keys must be atomic with the side effect (transaction or compare-and-set)
- TTL longer than the client's retry window
- Keys are unguessable enough to prevent cross-tenant replay if they are secret-like; bind to authenticated principal

## Failure considerations
If the process crashes after side effect and before storing the key, a retry may double-apply. Design the side effect itself to be unique-constrained (e.g. unique payment intent id).

## Security
Do not put secrets in keys that get logged. Authorize before applying. Cross-tenant key reuse must fail.

## Verification
Two identical POSTs with one key produce one side effect. Mismatched body with the same key is rejected. Tests should not require production payment processors.
