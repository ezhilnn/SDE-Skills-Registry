# Process Health Checks

## Intent
Expose liveness and readiness so orchestrators restart or stop routing correctly.

## When to use
Any long-running service behind a load balancer or kube probe.

## Distinctions
- **Liveness:** process is deadlocked or wedged → restart
- **Readiness:** process should not receive traffic (warming, dependency down if that is your policy)
- **Startup:** slow boot without killing the process

Do not make liveness depend on a downstream database if a DB blip would restart the whole fleet.

## Constraints
- Cheap, bounded time
- No authentication that requires user credentials
- No secret leakage in response bodies
- Distinct endpoints or probe configs for live vs ready

## Failure considerations
A ready check that requires every dependency will flap with downstream noise. A live check that is too strict causes CrashLoopBackOff.

## Security
Health endpoints should not dump config, versions with vulnerable fingerprints if policy forbids, or internal URLs. Bind appropriately.

## Verification
Probe failure removes the instance from service. Process hang is detected by liveness without requiring a downstream outage.
