# HTTP Contract Tests

## Intent
Verify that a provider's API still matches a consumer's expectations without running the full UI.

## When to use
Multiple services sharing an HTTP contract; public API versioning.

## Pattern
- Consumer or shared spec (OpenAPI, Pact, or equivalent) defines request/response shapes and status codes
- Provider verifies the spec against a test instance
- Breaking changes fail CI on the provider before deploy

## Constraints
- Auth in tests uses disposable credentials or test doubles, never production `<API_KEY>`
- Specs versioned with the API
- Examples in the spec use placeholders, not live tokens

## Failure considerations
Contract tests that always hit production are not contract tests. Flaky network to a shared staging makes the suite a flake source — prefer Testcontainers or in-process servers.

## Security
Do not commit production URLs with embedded credentials. Schema tests should include rejection of oversized payloads if that is part of the contract.

## Verification
A field removal or status-code change fails the provider job. A matching implementation passes on a disposable server.
