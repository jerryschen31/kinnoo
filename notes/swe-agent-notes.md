# Running notes for Software Engineer Agents (swe.agent.md)

## Root Cause of UnboundLocalError in kinnoo CLI
- The root cause of the UnboundLocalError in your CLI code is referencing the variable args before it is assigned by parser.parse_args(). For example:
- Here, args is not defined until after parser.parse_args() is called. If the first if-block is not entered, the elif tries to access args before it exists, causing the UnboundLocalError.

### Why does this keep coming up?
- Python only assigns args after parser.parse_args() runs.
- Any code path that references args before that assignment will fail.
- Mixing sys.argv pre-parsing and args-based logic in the same if/elif/else block is error-prone, especially if you return or exit early in some branches but not others.

### How to fix it
- Only use sys.argv for pre-parsing usage errors, and do not reference args in the same if/elif/else block.
- After parser.parse_args(), use args exclusively for subcommand dispatch.
- Keep pre-parse usage checks and main logic separate.
- Do all sys.argv checks before calling parser.parse_args().
- After parser.parse_args(), only use args for logic.
- This will prevent UnboundLocalError and make your CLI more robust and maintainable.