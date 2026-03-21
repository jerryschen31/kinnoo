# Task249 - feature44 agents page clickable names + right-side manifest table

## Summary
- Implemented Name-column links on the Agents page so each agent name is clickable and points back to `/agents` with selection query params.
- Extended `GET /agents` in `server/routes/web_agents.py` to accept `selected_tenant` and `selected_agent`, then load the selected agent's latest manifest metadata.
- Added a right-side details panel to `server/templates/agents.html` that renders a key/value table for canonical kinnoo.yaml schema fields.
- Added safe fallback rendering (`N/A`) for missing optional/unknown values.
- Added mapped test `server/tests/test_web_agents.py::test_agents_name_click_shows_right_panel_manifest_schema`.

## Files changed
- `server/routes/web_agents.py`
- `server/templates/agents.html`
- `server/tests/test_web_agents.py`
- `TASKS.txt` (task249 status updated to `needs-review`)

## Tests run (targeted only)
- `python3 -m pytest server/tests/test_web_agents.py::test_agents_name_click_shows_right_panel_manifest_schema server/tests/test_web_agents.py::test_listing_and_search -q`
- Result: `2 passed`

## Teaching notes
- A good way to implement "show details on same page" in server-rendered apps is query-driven state (`selected_tenant`, `selected_agent`) rather than JavaScript-heavy state management; this keeps behavior deterministic and very testable.
- For evolving schemas, rendering a canonical field-path list plus `N/A` fallback gives stable UX and protects against partial manifests.
- In acceptance-test-driven work, pair one new focused regression test with one nearby existing test to verify additive behavior without broad-suite runtime cost.
