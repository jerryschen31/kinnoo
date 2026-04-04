# Feature 91 — SWE Handoff: Production-Grade Rate Limiting

## Context
Enhance the existing rate limiter in `server/middleware.py` with per-tenant limits, endpoint-specific configs, and standard rate limit headers.

## Files to Modify
- `server/middleware.py` (~165 lines) — `RateLimitRule`, `InMemoryRateLimiter`, `PathRateLimitMiddleware` already exist. Enhance with:
  - Per-tenant rate limiting (extract tenant from JWT claims)
  - Endpoint group configuration (auth, publish, search/download)
  - Standard headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
  - `Retry-After` header on 429 responses
- `server/config.py` — Add rate limit configuration values

## Rate Limit Defaults
| Endpoint Group | Limit | Window | Key |
|---------------|-------|--------|-----|
| Auth (/login, /register) | 5 req | 1 minute | IP |
| Publish (/publish) | 10 req | 1 hour | tenant |
| Search/Download (/search, /download) | 60 req | 1 minute | IP |

## Implementation Notes
- Existing `InMemoryRateLimiter` uses a sliding window — keep this approach
- Tenant extraction: parse JWT from Authorization header, use `tenant` claim as key
- If no JWT (unauthenticated), fall back to IP-based rate limiting
- Rate limit headers should be on ALL responses (not just 429)
- In-memory rate limiting is acceptable for single-instance beta

## Testing
- Verify auth endpoints are limited to 5/min per IP
- Verify publish limited to 10/hour per tenant
- Verify X-RateLimit-* headers present on all responses
- Verify Retry-After header on 429 responses
- Verify rate limits reset after window expires

## Dependencies
- None (existing middleware is enhanced)

## Acceptance Criteria Summary
1. Configurable per-endpoint-group rate limits
2. Per-IP and per-tenant limiting
3. Standard rate limit headers on all responses
4. Retry-After on 429
