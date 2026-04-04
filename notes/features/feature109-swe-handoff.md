# Feature 109 — SWE Handoff: Forgot Password Flow

## Context
Add forgot-password endpoint that logs the request and fires an SNS notification to Jerry. NO automated email — Jerry manually resets via admin CLI.

## Files to Modify
- `server/routes/auth.py` or create `server/routes/password.py` — New endpoint:
  - `POST /forgot-password` accepts `email` parameter
  - Always returns 200 with generic message (prevent email enumeration)
  - If email exists: log + fire SNS notification
  - If email doesn't exist: log only (no SNS, prevent abuse)
- `server/routes/web_auth.py` — Add forgot password web page:
  - Link on login page: "Forgot your password?"
  - Form: email field + submit button
  - Success message: "If an account exists, the admin has been notified"
- `server/config.py` — Add `SNS_PASSWORD_RESET_TOPIC_ARN` config

## SNS Notification Format
```json
{
  "event": "password_reset_requested",
  "email": "user@example.com",
  "timestamp": "2026-04-04T12:00:00Z",
  "source_ip": "1.2.3.4"
}
```

## Full Workflow
1. User clicks "Forgot Password?" on login page
2. User enters email → `POST /forgot-password`
3. Server logs request + fires SNS (if email exists)
4. Jerry gets email notification from SNS
5. Jerry runs: `kinnoo-server user reset-password --email user@example.com`
6. Jerry sends temporary password to user manually

## Implementation Notes
- Use `boto3` SNS client to publish to the password reset topic
- SNS topic ARN from environment variable (set in Terraform feature107)
- Rate limit: max 3 forgot-password requests per IP per hour
- Response is always the same regardless of whether email exists (anti-enumeration)
- If SNS is not configured (dev mode), log the notification instead

## Testing
- Valid email → 200 + SNS notification sent (mock SNS)
- Invalid email → 200 + no SNS (log only)
- Rate limiting works (4th request → 429)
- Web form renders and submits correctly

## Dependencies
- feature102 (admin CLI for password reset)
- feature107 (SNS topic for notifications)

## Acceptance Criteria Summary
1. POST /forgot-password always returns 200
2. SNS notification for existing emails
3. No email enumeration
4. Rate limited (3/hour/IP)
5. Web page with forgot password form
