# Feature 94 — SWE Handoff: Security Model Document

## Context
Document kinnoo's security architecture for transparency and trust.

## Files to Create
- `docs/security-model.md`

## Content Structure
1. **Threat Model** — Key threats: supply-chain attacks, tampered archives, credential theft, abuse
2. **Signing Model** — Ed25519 key generation, signing workflow, verification, trust store
3. **Integrity Verification** — META-INF/integrity.json, file hashing, install-time checks
4. **Authentication** — JWT flow, Argon2id hashing, token lifecycle, session management
5. **Authorization** — Tenant isolation, resource ownership
6. **Transport Security** — HTTPS, CORS, Cloudflare proxy
7. **Rate Limiting** — Per-IP, per-tenant, endpoint groups
8. **Upload Validation** — Size, format, manifest, integrity checks
9. **Password Policy** — Minimum length, complexity, lockout
10. **Responsible Disclosure** — How to report vulnerabilities

## Implementation Notes
- Reference: `src/kinnoo/signing.py`, `server/auth/token.py`, `server/auth/session.py`
- Should be accurate to the implemented state (after Phase 8 and 9)
- Include diagrams where helpful (Mermaid or ASCII art)

## Dependencies
- feature86, feature87, feature88 (integrity/signing — should be implemented for accuracy)

## Acceptance Criteria Summary
1. docs/security-model.md with complete security architecture
2. Threat model with mitigations
3. Cross-referenced from README.md
