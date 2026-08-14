# Structured Logging with Correlation IDs

## Intent
Emit machine-parseable logs that can join a single request across services without dumping payloads.

## When to use
Request-handling services, workers processing a message with a trace or correlation id.

## Constraints
- One event per log line (JSON or equivalent)
- Fields: timestamp, severity, service, correlation_id / trace_id, span_id, event name
- Errors include exception type and stack only where policy allows
- Cardinality: do not log unbounded user-generated strings as labels/metrics

## Failure considerations
Synchronous logging to a slow disk can stall request threads. Prefer non-blocking appenders with drop/metrics on overflow.

## Security
Never log Authorization headers, cookies, tokens, passwords, or full request bodies by default. Redact known secret keys. Correlation IDs must not be equivalent to session secrets.

## Verification
A known request id retrieves the path through gateway → service → dependency logs. A test request with a fake `Authorization: Bearer <ACCESS_TOKEN>` does not appear in log sinks.
