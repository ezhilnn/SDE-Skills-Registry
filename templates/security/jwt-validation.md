# JWT Access-Token Validation

## Intent
Authenticate a request using a signed JWT without implementing a homegrown crypto scheme.

## When to use
Service-to-user or service-to-service calls that already issue JWTs from a known issuer.

## When not to use
Passing JWTs in query strings, using `alg: none`, or trusting unsigned claims for authorization.

## Constraints
- Verify signature against the issuer's current keys (JWKS), with key-id
- Validate `iss`, `aud`, `exp`, `nbf`
- Clock skew bound (small)
- Algorithm allow-list; reject `none`
- Authorization is a separate step (roles/scopes/resource)

## Failure considerations
JWKS fetch failure should fail closed for authentication, with timeouts so an IdP outage does not hang all workers forever. Cache keys with TTL and SWR, not forever.

## Security
- Do not log the token
- Do not accept tokens from the body of GET query params
- Do not use the same token as a CSRF defense for cookies unless the architecture is designed for it
- Rotate keys; handle `kid` miss as unauthenticated, not as a crash loop of 500s if that would hide attacks — prefer 401

## Verification
Expired, wrong audience, wrong issuer, and tampered signature each yield 401. A valid token with missing scope yields 403, not 401, if that is the API contract.
