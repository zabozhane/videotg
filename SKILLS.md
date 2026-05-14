# Skills Context

## Selection Rationale
- Selected telegram_bot because the spec mentions bot/telegram workflows.
- Selected python_async to enforce reliable async patterns in Python services.

## Selected Skill Packs
### Telegram Bot (`telegram_bot`)
Reusable engineering context pack with: architecture, pitfalls, rules.

Source: local_pack | Confidence: high
Match reason: Matched by local skill keyword rules.

Rules:
- Keep bot handlers idempotent and safe for retries.
- Validate incoming update payloads before processing.
- Separate transport concerns (Telegram API) from domain logic.
- Log failed Telegram API calls with request context.

Conventions:
- None

Architecture guidance:
- Use a thin Telegram adapter layer for polling/webhook updates.
- Route parsed updates into explicit application use-cases.
- Keep command handlers small and side-effect aware.

Common pitfalls:
- Mixing long-running work directly in update handlers blocks responsiveness.
- Ignoring rate limits can get bot requests throttled.
- Relying on mutable in-memory session state breaks after restarts.

Prompts:
- None

### Python Async (`python_async`)
Reusable engineering context pack with: pitfalls, rules.

Source: local_pack | Confidence: high
Match reason: Matched by local skill keyword rules.

Rules:
- Never block the event loop with sync I/O in coroutine paths.
- Bound concurrency with semaphores or worker pools.
- Propagate cancellation and timeouts intentionally.
- Use structured retries with jitter for flaky network calls.

Conventions:
- None

Architecture guidance:
- None

Common pitfalls:
- Fire-and-forget tasks can hide exceptions and leak resources.
- Shared mutable state across coroutines causes race conditions.
- Unbounded gather() calls can overload external services.

Prompts:
- None

