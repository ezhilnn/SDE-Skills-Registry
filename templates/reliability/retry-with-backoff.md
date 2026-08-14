# Retry with Bounded Backoff

Production-oriented pattern. Complements reliability work; it is not a skill.

## Intent
Retry a failed *idempotent* dependency call without amplifying outages.

## When to use
Transient network errors, 429, 503, and timeouts on idempotent reads or explicitly idempotent writes (Idempotency-Key).

## When not to use
Non-idempotent POST without an idempotency key, 4xx other than 429, authentication failures, business-rule rejections.

## Constraints
- Max attempts (small, e.g. 3–5)
- Exponential backoff with jitter
- Overall deadline inherited from the parent request
- Retry only classified transient errors
- Do not retry after cancellation
- Log attempt count and last error without secrets

## Failure considerations
Retries multiply load. Pair with timeouts, bulkheads, and circuit breaking on sustained error rate. Honor `Retry-After`.

## Security
Do not retry with a refreshed secret in logs. Do not send the same mutating request twice unless the server contract is idempotent.

## Verification
Chaos or fault-injection tests: transient 503 eventually succeeds within budget; 400 is not retried; deadline abort is observed.
