# Registry Guide

This guide covers invite-only registry usage for publishing and consuming agents.

## 1) Invite-Only Account Setup

The registry is invite-only. An operator must create your account/invite before you can log in.

## 2) Configure Registry Endpoint

```bash
export KINNOO_REGISTRY_URL=https://dev-api.kinnoo.ai
```

## 3) Log In

Interactive login:

```bash
kinnoo login
```

Expected output (example):

```text
Login successful.
Registry: https://dev-api.kinnoo.ai
Tenant: <your-tenant>
```

Non-interactive login:

```bash
kinnoo login --email user@example.com --password 'your-password'
```

## 4) Publish an Agent

Publish latest archive source by name:

```bash
kinnoo publish my-agent --remote
```

Expected output (example):

```text
Published my-agent==<version> (remote)
Remote publish result: ...
```

Pack and publish from directory:

```bash
kinnoo publish ./my-agent --pack --bump patch --remote
```

Pack and publish with strict trust gates (recommended for team/shared registries):

```bash
kinnoo publish ./my-agent --pack --strict --remote
```

By default, pack/publish uses public visibility unless your manifest explicitly sets `visibility: private`.

Force private visibility during pack/publish:

```bash
kinnoo publish ./my-agent --pack --private --remote
```

## 5) Search and List

```bash
kinnoo list --remote
kinnoo search my-agent --remote
```

Expected output (example):

```text
Remote registry agents:
- my-agent  <latest-version>
```

## 6) Install from Registry

Latest version:

```bash
kinnoo install my-agent --remote
```

Expected output (example):

```text
[kinnoo install] Installing my-agent...
[kinnoo install] Completed.
```

Exact version:

```bash
kinnoo install my-agent==1.2.3 --remote
```

Strict trust install:

```bash
kinnoo install my-agent --remote --strict
```

## 7) Fetch Without Installing (Optional)

Use fetch when you want local archive mirroring, offline review, or deferred install:

```bash
kinnoo fetch my-agent==1.2.3 --remote --strict
```

Install that fetched version later from local archive resolution:

```bash
kinnoo install my-agent==1.2.3 --local --strict
```

## 8) Sign and Verify (Recommended)

```bash
kinnoo keygen
kinnoo pack ./my-agent --sign ./kinnoo-ed25519-private.pem
kinnoo publish ./my-agent --pack --strict --remote
```

## 9) Log Out

```bash
kinnoo logout
```

## 10) Auth Environment Contract (feature118)

For OIDC/Kinde cutover environments, use canonical provider-neutral `AUTH_*` keys.
Kinde-prefixed keys remain temporary compatibility aliases and are loaded only when the canonical key is absent.

- Canonical keys:
  - `AUTH_PROVIDER`
  - `AUTH_ISSUER_URL`
  - `AUTH_JWKS_ENDPOINT_URL`
  - `AUTH_TOKEN_ENDPOINT`
  - `AUTH_AUTHORIZATION_ENDPOINT`
  - `AUTH_LOGOUT_ENDPOINT`
  - `AUTH_USERINFO_ENDPOINT`
  - `AUTH_REVOCATION_ENDPOINT` (optional)
  - `AUTH_AUDIENCE`
  - `AUTH_WEB_CLIENT_ID`
  - `AUTH_WEB_CLIENT_SECRET`
  - `AUTH_CLI_CLIENT_ID`
  - `AUTH_WEB_REDIRECT_URI`
  - `AUTH_LOGOUT_REDIRECT_URI`

Legacy local password/register/reset API paths are disabled by default when `AUTH_PROVIDER` is OIDC-backed.
For temporary rollback only, set:

```bash
export AUTH_ENABLE_LEGACY_PATHS=true
```
