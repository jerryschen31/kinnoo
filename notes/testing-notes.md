Recommended strategy for testing agents that use NodeJS:

1. Keep pytest for all Kinnoo contract/integration tests:
  - run/pack/install behavior for Node agents
  - manifest acceptance/rejection for runtime.language nodejs and future fields
  - preflight checks for node version and package manager availability
  - regression safety for Python flows

2. Add Node-based tests only when you introduce real JS/TS code that Kinnoo owns:
  - shared JS utilities
  - generated OpenClaw template logic you want to validate as code, not just black-box CLI behavior
  - TS transpilation helpers (if you later add them)
  - If you do add Node tests, current standard in JS/TS is:

3. JS/TS testing frameworks
  - Vitest (most common modern choice, fast, TS-friendly)
  - Node built-in test runner node:test (good lightweight option, fewer extras)
  - Jest (still common, but less preferred for new greenfield setups than Vitest)
  - Playwright (only for browser/UI E2E, if you ever have web UI components)

4. Practical decision rule ([note to agent] go with this)
  - If testing Kinnoo behavior from the outside, use pytest.
  - If testing internal JS/TS implementation details, use Vitest.
  - It is fine to have both, but keep pytest as the top-level release gate for this repo.