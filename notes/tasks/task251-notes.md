# Task251 - Remote list/search summary-shape compatibility fix

## Context
A scratch publish run succeeded, but the follow-up remote list step crashed with:
`AttributeError: 'dict' object has no attribute 'description'`.

The failure occurred because remote API-backed summary items were dict-shaped, while
CLI rendering paths in `list_command` and `search_command` expected object attributes.

## Implementation
- Updated `src/kinnoo/list_command.py` to normalize summary field access across dict and object summary shapes.
- Updated `src/kinnoo/search_command.py` with the same summary-shape normalization logic.
- Added focused regression tests in `tests/test_cli_remote_summary_shape.py`:
  - `test_list_remote_accepts_dict_summaries`
  - `test_search_remote_accepts_dict_summaries`

## Validation
- Ran targeted regressions only:
  - `python3 -m pytest tests/test_cli_remote_summary_shape.py tests/test_cli_registry_modes.py::test_list_default_local_and_remote_modes -q`
- Result: `3 passed`.

## Outcome
Remote publish + list/search flows now handle remote dict-shaped summary payloads safely,
while preserving compatibility for existing object-based summary flows.

## Teaching Notes
- Contract boundaries between service and presentation layers should either enforce a single canonical type or normalize adapter inputs at render boundaries.
- Backward-compatible normalizers (`dict` + object access) are effective for migrations where multiple summary representations may coexist.
- Regressions for both the direct bug path and one neighboring baseline path reduce the chance of fixing one branch while breaking another.
