# task522 implementation notes

- Added `web/wrangler.prod.jsonc`: same worker `name: "kinnoo"` and `WORKER_SELF_REFERENCE` self-binding as dev (so the Open-Next adapter still resolves), but routes `kinnoo.ai` and `www.kinnoo.ai` as custom domains and pins `vars.BACKEND_URL` to `https://api.kinnoo.ai`.
- Added `deploy:prod` npm script in `web/package.json` that runs `opennextjs-cloudflare deploy -- --config wrangler.prod.jsonc`. Dev `deploy` script unchanged.
- Added `web/__tests__/wrangler-prod-config.test.ts` (test745): vitest config-parse test asserting prod config targets prod domains, preserves bindings, and contains no dev references; also asserts dev wrangler config is still dev-targeted.
