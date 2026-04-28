# Getting Started

If you are building AI agents and want a reliable way to package, publish, install, and run them, Kinnoo gives you a consistent lifecycle from local dev to registry distribution.

This guide is intentionally hands-on: in under ~10 minutes, you will install Kinnoo, scaffold an agent, run it locally, package it, publish it, and install it from the registry.

## Prerequisites

- Python 3.11+
- `pip`

## 1) Install Kinnoo

Start with a clean virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
pip install kinnoo
```

## 2) Set Up Your Kinnoo Environment

For Kinnoo registry workflows, the only required environment variable to set manually is the registry endpoint:

```bash
export KINNOO_REGISTRY_URL=https://api.kinnoo.ai
```

Why this is enough:

- `KINNOO_REGISTRY_URL` tells Kinnoo which hosted registry/auth service to use.
- `kinnoo login` then discovers hosted auth settings and stores your token + tenant context locally.
- You do **not** need to manually set `KINNOO_REGISTRY_TOKEN` or `KINNOO_TENANT_SLUG` for normal interactive usage.

Note: your agent framework may still require provider-specific secrets (for example OpenAI/Anthropic/Gemini keys) to run your agent logic.

## 3) Initialize Your First Agent

Create a starter project:

```bash
kinnoo init chatgpt my-agent
```

This generates a scaffold in `./my-agent`, including `kinnoo.yaml`.

## 4) Run Locally

Try a normal local run:

```bash
kinnoo run ./my-agent "hello"
```

If you only want a quick readiness check:

```bash
kinnoo run ./my-agent --preflight
```

If your manifest uses `entrypoints`, you can target one explicitly:

```bash
kinnoo run ./my-agent --entrypoint scripts/main.py "hello"
```

## 5) Package Your Agent

Create a `.kno` archive:

```bash
kinnoo pack ./my-agent
```

Optional: create signing keys and package with a detached signature:

```bash
kinnoo keygen
kinnoo pack ./my-agent --sign ./kinnoo-ed25519-private.pem
```

## 6) Log In and Publish

Authenticate once:

```bash
kinnoo login
```

Then publish from your agent directory with pack + strict trust gates:

```bash
kinnoo publish ./my-agent --pack --strict --remote
```

## 7) Install from Registry

Install your published agent from the remote registry:

```bash
kinnoo install my-agent --remote --strict
```

You now have a complete lifecycle path: `init -> run -> pack -> publish -> install`.

## Quick Troubleshooting

### Installation and setup

- **`kinnoo: command not found`**: activate your venv (`source .venv/bin/activate`) and reinstall (`pip install kinnoo`).
- **Login/auth discovery failure**: confirm `KINNOO_REGISTRY_URL` is exactly `https://api.kinnoo.ai`.

### Agent initialization

- **Directory already exists**: choose a new agent name or remove the existing folder.
- **Unsupported framework**: check supported templates in `docs/supported-agents.md`.

### Local run

- **Manifest validation errors**: run `kinnoo inspect ./my-agent` and fix required `kinnoo.yaml` fields.
- **Provider auth errors**: set the framework-specific API key expected by your agent template.

### Packaging

- **Pack fails on missing files/invalid manifest**: rerun `kinnoo inspect ./my-agent` and verify `entrypoint`/`entrypoints` paths.
- **Signature errors**: regenerate keys with `kinnoo keygen` and use a valid private key path with `--sign`.

### Publishing

- **Unauthorized/forbidden**: run `kinnoo login` again, then retry publish.
- **Version conflict**: bump version in `kinnoo.yaml` or publish with `--bump patch`.

## Next Steps

- Registry workflows and team sharing: `docs/registry-guide.md`
- Manifest field reference: `docs/kinnoo-yaml-spec.md`
- Trust and verification model: `docs/security-model.md`
