# Task245 - feature30 Jinja2 template setup + base layout

## Summary
- Configured template and static support in `server/app.py`:
  - Added `Jinja2Templates` initialization and stored it on `app.state.templates`.
  - Mounted static files from `server/templates/static` at `/static`.
- Added base layout template in `server/templates/base.html` with required structural sections:
  - header
  - nav
  - content block (`{% block content %}`)
  - footer
- Added baseline stylesheet in `server/templates/static/style.css` to provide a clean, consistent UI foundation.
- Added mapped test343 implementation in `server/tests/test_templates.py::test_base_layout`.

## Tests and results
- `python3 -m pytest server/tests/test_templates.py::test_base_layout` -> `1 passed`

## Bug/error notes
- Bug class: missing Jinja2 runtime dependency when creating `Jinja2Templates` (`AssertionError: jinja2 must be installed`).
- Attempts for this bug class: `1` (cap: `5`).
- Resolution: added `jinja2>=3.1.0` to `requirements.txt` and `server/requirements.txt`, then installed deps and reran mapped test.

## Teaching notes
- FastAPI uses Starlette templating under the hood, and `Jinja2Templates` performs an import-time/runtime check for Jinja2. Even if FastAPI is installed, template support still requires explicit `jinja2` dependency management.
- Storing template engine configuration in app state (`app.state.templates`) creates a stable, test-friendly contract for future route handlers and keeps template loading centralized.
- Building a minimal base template with Jinja blocks early makes downstream web-route tasks simpler because each page can focus on content rather than repeating layout concerns.
