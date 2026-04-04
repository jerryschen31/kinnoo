# Feature 90 — SWE Handoff: Server-Side Upload Validation

## Context
Validate uploaded `.kno` archives on the server before storing in S3. Currently `server/routes/publish.py` has minimal validation.

## Files to Modify
- `server/routes/publish.py` (~250 lines) — Add validation pipeline in `publish_archive()`:
  1. Check Content-Length against max upload size (configurable, default 100MB)
  2. Verify file is a valid zip archive
  3. Extract and validate `kinnoo.yaml` (required fields: name, version, framework)
  4. If `META-INF/integrity.json` is present, verify hashes match archived files
  5. Reject with descriptive JSON error on any failure
- `server/config.py` — Add `MAX_UPLOAD_SIZE_MB` config (default: 100)

## Validation Order (fail fast)
1. Size check (no need to read full file if oversized) → 413
2. Zip format check → 400
3. kinnoo.yaml presence → 400
4. kinnoo.yaml field validation → 400
5. Integrity manifest verification (if present) → 400
6. Pass → proceed with S3 upload

## Error Response Format
```json
{
  "error": "upload_validation_failed",
  "detail": "Archive is missing required file: kinnoo.yaml",
  "code": 400
}
```

## Testing
- Oversized upload → 413
- Non-zip file → 400
- Missing kinnoo.yaml → 400
- Invalid kinnoo.yaml (missing name) → 400
- Tampered archive with valid integrity.json → 400
- Valid archive → upload proceeds

## Dependencies
- feature86 (integrity module for server-side verification)

## Acceptance Criteria Summary
1. Rejects oversized uploads (413)
2. Rejects non-zip files (400)
3. Rejects missing/invalid kinnoo.yaml (400)
4. Validates integrity.json if present
5. Descriptive JSON error responses
