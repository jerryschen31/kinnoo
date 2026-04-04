# Feature 112 — SWE Handoff: Registry Seeding & Validation

## Context
Publish 3-5 real agents to the registry and validate the full workflow. Primarily operator work — SWE creates documentation and helper scripts.

## Files to Create
- `docs/registry-seeding.md` — Documentation for seeding process
- `scripts/seed_registry.sh` (optional) — Helper script for seeding

## Seeding Plan
| Agent | Framework | Signed | Description |
|-------|-----------|--------|-------------|
| hello-chatgpt | chatgpt | Yes | Basic ChatGPT conversational agent |
| hello-openai | openai | No | OpenAI API-based agent |
| hello-gemini | gemini | Yes | Google Gemini agent |
| hello-generic | generic | No | Framework-agnostic example |

## Validation Steps (per agent)
1. `kinnoo pack <agent> --sign` → verify .kno created with META-INF/
2. `kinnoo publish <agent> --remote` → verify upload succeeds
3. `kinnoo search <agent> --remote` → verify agent appears in results
4. `kinnoo install <agent> --remote --strict` → verify install + verification
5. `kinnoo run <agent> "test"` → verify execution (API key required for non-generic)

## Documentation Content
- Step-by-step seeding process
- How to create a new seed agent from scratch
- How to update/version-bump a seed agent
- Troubleshooting common issues

## Implementation Notes
- This is primarily Jerry's work — SWE provides the documentation and scripts
- Seed agents should be simple, well-commented examples
- At least one agent must be signed (to validate integrity/signature chain)
- Agent source code can live in `examples/` directory

## Dependencies
- feature86, feature87, feature88 (integrity/signature for signed agents)
- feature89, feature90 (server must validate uploads)

## Acceptance Criteria Summary
1. 3+ agents published covering different frameworks
2. Each searchable, installable, runnable
3. At least one signed
4. docs/registry-seeding.md documents the process
