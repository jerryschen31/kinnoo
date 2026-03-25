# Phase 5 - Web Frontend and Registry Frontend + Backend

## Overview
The kinnoo web frontend is a clean, simple, aesthetically-pleasing, developer-friendly website that introduces kinnoo as a developer platform for packaging and sharing agents. The main webpage should allow for easy access to registry login, Github repository, docs, and reporting issues. After login, the user should be taken to a user registry that shows a user's published agents. Within the registry, the user can also search for other published public agents, with each published agent showing a Terminal-like graphic that shows the full kinnoo CLI command for installing that agent. For this phase, the registry and associated agent metadata use an S3 backend with IAM policies attached to properly restrict access to user folders. Both the web frontend and registry have proper security and access controls to prevent denial-of-service and bot-based attacks attempting to steal credentials. The web API is securely designed - does not expose tokens or credentials that would be deemed a security vulnerability.

The front-page is a single page with a hamburger bar at the top-left that, when clicked, shows three links: 1) Github repo, 2) Docs, 3) Report an Issue. The top-right is a Login button that, when clicked, will go to a separate login page with username and password fields. Once logged in, the user is taken to the user's main registry page, where the user can see a list of his/her published agents. There is a nav bar at the top with the following buttons: "My Agents", "Search", "Logout".

Website should be desktop-first, but webpages should render and be usable on mobile device browsers as well.

## Sub-phases
### Sub-phase 1 - Frontend Setup
Prompt 1: The Foundation & Design System
Objective: Set up the Next.js 15+ environment, the Radix UI theme, and the global layout (Hamburger & Login).
Role: Lead Frontend Architect.
Task: Initialize a Next.js (App Router) project with TypeScript and Tailwind CSS v3.

Design Specification: > - Theme: Dark Mode by default. Background #000000, text #F9FAFB. Kinnoo logo: #3B82F6

Aesthetic: 
- OpenClaw-inspired. Use 1px borders (border-white/10) and subtle glassmorphism (backdrop-blur).
- For font, use "Avenir Next", with "Segoe UI" and generic "sans-serif" as fallback, as done in the server/

Layout: Create a MainLayout with:

Top-Left: A Hamburger menu (Lucide icon) that opens a sheet/drawer with links: 1) GitHub, 2) Docs, 3) Report an Issue.

Top-Right: A "Login" button using a minimalist ghost-button style.

Design Tokens:
- Border-radius: 8px (cards), 4px (buttons/inputs)
- Surface color: #111111 (cards, modals)
- Card border: rgba(255,255,255,0.1)
- Heading sizes: h1 48px, h2 32px, h3 24px, body 16px
- Spacing unit: 4px (use multiples: 8, 12, 16, 24, 32, 48)
- Use standard Tailwind breakpoints: sm (640px), md (768px), lg (1024px)

Requirements: 
- Use Radix UI primitives for the Menu and Buttons to ensure accessibility. Define a global ThemeConfig that the AI can reference for all future components.
- Use npm as package manager.
- The Next.js project must be initialized in a top-level `web/` directory, separate from the Python codebase and `server/` directory.

Directory structure (inside web/):
```
web/                          # Next.js project root
├── app/
│   ├── (public)/             # Public routes (no auth required)
│   │   ├── page.tsx          # / (landing page)
│   │   ├── login/page.tsx    # /login
│   │   └── signup/page.tsx   # /signup
│   ├── (auth)/               # Authenticated routes (session guard in layout)
│   │   ├── layout.tsx        # Checks session cookie, redirects to /login on 401
│   │   └── registry/page.tsx # /registry (My Agents + Search)
│   └── layout.tsx            # Root layout with MainLayout
├── components/
│   ├── ui/                   # Primitives: Button, Card, Sheet, Modal, Input
│   └── blocks/               # Sections: HeroSection, FeatureGrid, AgentCard, TerminalPreview
├── lib/                      # API client helpers, auth utils, constants
└── __tests__/                # Component and integration tests
```
Use Next.js route groups `(public)` and `(auth)` to apply different layouts and auth guards. We might need other directories later, but this is the foundation.

Tests: Write smoke tests that verify the root layout renders with the hamburger menu and Login button, and that the ThemeConfig design tokens are applied.

### Sub-phase 2 - Landing Page and Secure Login UI
Prompt 2: The Landing Page & Secure Login UI
Objective: Build the public "pitch" page and the credential entry screen.
Role: Senior UI/UX Engineer.
Task: Build the Landing Page and the Login Page.

Landing Page (/):
- Create a hero section with a clean, high-contrast title: "Package, publish, share your AI agents with the world"
- Add a sub-headline: "Take any AI agent — a LangGraph chatbot, a PydanticAI workflow, an OpenClaw daemon — and give it a portable, version-controlled, signed package that anyone can install and run"
- Feature a "Terminal Preview" component showing "pip install kinnoo" as the one-line command to install kinnoo CLI. Terminal Preview should just be a minimal code block with a copy button for copying to clipboard.
- Below the hero section and Terminal component, add a "Features" section that shows six hoverable boxes with the following header + subtext:
Feature 1 Header: Supports common AI agent frameworks
Feature 1 Subtext: Initialize, import or install AI agents developed with LangChain, LangGraph, PydanticAI, OpenAI Agents SDK, OpenClaw and more.

Feature 2 Header: One-command packaging
Feature 2 Subtext: Bundle your agent, its dependencies, assets, and state into a single portable .kno archive — ready to share or publish.

Feature 3 Header: Discover and install from a registry
Feature 3 Subtext: Publish agents to a hosted registry where others can search, inspect, and install them with kinnoo install — like npm, but for agents.

Feature 4 Header: Built to run real-world agents
Feature 4 Subtext: kinnoo handles environment setup, dependency isolation, and runtime wiring for Python and Node.js agents, including one-shot and long-running daemon-based agents.

Feature 5 Header: Security built-in
Feature 5 Subtext: Signed archives, permission declarations, static security sweeps, dependency audits, preflight checks, runtime monitoring, and a kill switch — trust what you run.

Feature 6 Header: Inspect before you run
Feature 6 Subtext: Review any agent's manifest, dependencies, environment variables, permissions, and services before installation — no surprises.

Login Page (/login):
- Build a centered, minimalist login card.
- Fields: Username (E-mail) and Password.
- Security Specs: Implement client-side validation. Login page should include a "Forgot Password" stub. Use existing login.html in server/ as a base.
- Ensure the Login button has a loading state for when the API is called.
- the Next.js frontend should use credentials: 'include' in fetch calls and rely on the existing session-cookie flow rather than storing tokens in localStorage/sessionStorage.
- Next.js API routes act as a BFF (Backend-for-Frontend) proxy to FastAPI.

Login Form Submission Flow:
1. The Next.js login page submits to FastAPI's POST /login via the rewrite proxy (the form action posts to /login, which the proxy forwards to FastAPI).
2. FastAPI validates the login CSRF token and credentials server-side.
3. On success, FastAPI returns a 303 redirect with Set-Cookie headers (kinnoo_session + kinnoo_csrf). The Next.js proxy must pass these Set-Cookie headers through to the browser.
4. The Next.js login page should intercept the redirect and send the user to /registry instead of FastAPI's default /agents redirect.

Tests: Write tests that verify the landing page renders the hero section, terminal preview, and all six feature cards. Write tests that verify the login form has the required fields, loading state, and client-side validation.

### Sub-phase 3 - Registry Dashboard
Prompt 3: The Registry Dashboard (Post-Login)

Objective: Create the "My Agents" and "Search" views with the command-copy functionality. Build upon what has already been built in server/

Role: Frontend Product Engineer.
Task: Build the Authenticated Dashboard (/registry).

Navigation Bar: Create a secondary Nav Bar for logged-in users with three buttons: "My Agents", "Search", and "Logout".

Views (State Controlled):
- My Agents: A grid of cards showing agents the current user has published.
- Search: A searchable gallery of all public agents + user's own agents. If the user wants to filter to search for only the user's agents, there is a "Show only my agents" checkbox next to the Search bar.

Agent Card Component (My Agents):
- Tenant, Name (clickable), Version, Author, Framework, Size, and Description.
- Clicking on Name shows a modal/dialog overlay showing the entire agent manifest (pulled from that agent's kinnoo.yaml). This modal has an 'X' at the top right that allows the user to close the modal.
- The existing API at /agents path already fetches the manifest via MetadataManager. The API endpoint the frontend should call is `GET /api/agents/{tenant_slug}/{agent_slug}`, which returns the agent's full version history and metadata. Note: there is no `{version}` path parameter on the detail route — it returns all versions for that agent.

Agent Card Component (All Public Agents - shown after a user successfully searches for agents among All Public Agents):
- Tenant, Name, Version, Author, Framework, Size, Description, 
- Clicking on Name shows a modal/dialog overlay showing the entire agent manifest (pulled from that agent's kinnoo.yaml). This modal has an 'X' at the top right that allows the user to close the modal. Also at the bottom of this modal is a terminal-like graphic that shows the kinnoo CLI command for installing this agent, with a "copy" button on the right for copy-to-clipboard for that install command text.

Requirement: 
- Use framer-motion for smooth transitions between the "My Agents" and "Search" tabs.
- Build upon what has already been built in server/ - don't reinvent the wheel!

Tests: Write component tests for the AgentCard component (renders all fields, name is clickable, modal opens/closes). Write a test that verifies the modal displays manifest data and the copy-to-clipboard button works for the install command.

### Sub-phase 4 - Integration, CSRF & Production Hardening
Prompt 4: Integration, CSRF & Production Hardening
Objective: Finalize the connection between Next.js and FastAPI, ensuring security headers and production readiness.
Role: Full-Stack & DevOps Engineer.
Task: Finalize the integration between the web frontend and the existing server/ backend.

Requirements:

Proxy Config: In next.config.ts, define rewrites that map /api/* to the FastAPI service 
(default http://localhost:8000). The destination URL must come from a BACKEND_URL environment 
variable, which will be changed once the kinnoo website goes live. Ensure rewrites preserve cookies (kinnoo_session, kinnoo_csrf) and forward X-Forwarded-For and X-Request-Id headers.

CSRF Integration: The existing FastAPI backend uses two CSRF mechanisms:
1. Login CSRF: A signed nonce embedded as a hidden form field, validated by 
   _validate_login_csrf_token in web_auth.py. The BFF proxy should forward the full form 
   submission to FastAPI which handles validation server-side.
2. Session CSRF: A non-HttpOnly cookie (kinnoo_csrf) set on login. For authenticated POST 
   requests (e.g., logout), the frontend must read this cookie via JavaScript and include 
   the token as a form field or X-CSRF-Token header. The backend's validate_post_request() 
   checks it against the session record.
Ensure both flows work correctly through the BFF proxy — cookies must not be stripped.

API Auth Compatibility: The existing JSON API routes (`/api/agents`, `/api/agents/{tenant_slug}/{agent_slug}`, `/api/search`) currently require Bearer token auth via the Authorization header. Add a fallback so these routes also accept the session cookie (`kinnoo_session`) for authentication. Modify `authenticate_request()` in `server/auth/middleware.py` to first check for a Bearer token, and if absent, fall back to validating the session cookie from the request. This allows the Next.js BFF to proxy calls without managing tokens separately.

Auth Check: Add a `GET /api/auth/me` endpoint to the FastAPI backend. This endpoint should validate the session cookie, retrieve the user record from `UserStore.get_by_id(session.user_id)`, and return `{ user_id, tenant_slug, username }` if valid, or 401 if not. Then implement a server-side check in `app/(auth)/layout.tsx` that calls this endpoint (forwarding cookies) and redirects to `/login` on 401.

Security Headers: Configure Next.js middleware (middleware.ts) to set:
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Referrer-Policy: strict-origin-when-cross-origin
- Content-Security-Policy with a restrictive default-src 'self'
- Strict-Transport-Security for production

Rate Limiting: Keep the existing InMemoryRateLimiter for development. Add a 
# TODO comment for Redis/Upstash migration. Ensure the Next.js proxy forwards 
X-Forwarded-For so the rate limiter keys on the real client IP, not the proxy.

Error States: Create error.tsx and loading.tsx for the (auth) route group to handle 
API downtime, 401, and 429 states gracefully with user-friendly messaging.

Environment Variables: The Next.js app requires:
- BACKEND_URL — FastAPI server URL (default http://localhost:8000)
- NODE_ENV — development or production
All S3 access goes through FastAPI. Do not add AWS credentials to the Next.js layer.

Tests: Write integration tests that verify the proxy rewrite forwards requests correctly, that CSRF tokens pass through the BFF, and that the auth check redirects to /login on 401. Write a test for the /api/auth/me endpoint.

Key Technical Clarifications for the Agent:
- Visibility: Use the existing visibility: "public" | "private" field in the metadata index. 
  Do not use S3 metadata tags.
- Directory: The backend code lives in /server. The Next.js frontend lives in /web.
- Node.js: Requires v20+.
- IAM: The S3 backend uses the existing prefix-scoped access logic in server/storage/. 
  Do not reimplement.
- continue to use the local mocked S3 storage for now. Make sure it is easy for me to point to actual S3 buckets once I decide to go live.
- Make me an admin account for the registry. My email and password are saved as REGISTRY_ADMIN_EMAIL and REGISTRY_ADMIN_PASSWORD in .env in the base project directory. Do NOT output my email or password in any of your agent thinking or output response.
- If possible make it so that executing ```kinnoo publish``` on my local machine actually publishes to an appropriate tenant folder location within the local mocked S3 storage. This way I can actually test publishing test agents from my local machine.

### Sub-phase 5 - User Registration & Password Reset
Prompt 5: User Registration & Password Reset Workflows
Objective: Implement a complete sign-up flow with email verification and a working password reset flow.
Role: Full-Stack Engineer.
Task: Build the registration and password reset pages and backend endpoints.

Sign-Up Flow:
1. Add a "Sign Up" button next to the "Login" button in the top-right of the MainLayout and on the login page.
2. Clicking "Sign Up" navigates to /signup.
3. The /signup page shows a centered, minimalist card (matching the login card style) with a single field: Email address. Include client-side validation (valid email format). A "Send Verification Link" button submits the form.
4. On submit, the frontend calls a new `POST /api/auth/register-request` endpoint on FastAPI, which:
   - Validates the email is not already registered.
   - Generates a time-limited, signed verification token (e.g., 24-hour expiry).
   - Sends an email containing a verification link: `{FRONTEND_URL}/signup/verify?token={token}`.
   - Returns 200 with a generic message ("If this email is valid, you'll receive a verification link") to avoid revealing whether the email exists.
5. The /signup page shows a confirmation message: "Check your email for a verification link."
6. Clicking the verification link navigates to /signup/verify?token={token}, which shows a card with:
   - "Create Password" field
   - "Confirm Password" field
   - Client-side validation: passwords must match, minimum 8 characters.
   - A "Create Account" button.
7. On submit, the frontend calls `POST /api/auth/register-confirm` with the token and password, which:
   - Validates and decodes the token (reject if expired or already used).
   - Creates the user via UserStore with a hashed password.
   - Creates a default tenant for the user (using the username/email prefix as the tenant slug).
   - Automatically logs the user in by creating a session and returning Set-Cookie headers.
   - Redirects to /registry.

Forgot Password Flow:
1. The "Forgot your password?" link on the login page navigates to /forgot-password.
2. The /forgot-password page shows a card with an Email field and a "Send Reset Link" button.
3. On submit, the frontend calls `POST /api/auth/password-reset-request`, which:
   - Looks up the user by email.
   - Generates a time-limited, signed reset token (e.g., 1-hour expiry).
   - Sends an email containing a reset link: `{FRONTEND_URL}/forgot-password/reset?token={token}`.
   - Returns a generic 200 message regardless of whether the email exists.
4. The /forgot-password page shows: "If an account exists with that email, you'll receive a reset link."
5. Clicking the reset link navigates to /forgot-password/reset?token={token}, which shows:
   - "New Password" field
   - "Confirm Password" field
   - A "Reset Password" button.
6. On submit, calls `POST /api/auth/password-reset-confirm` with the token and new password, which:
   - Validates and decodes the token.
   - Updates the user's password hash.
   - Invalidates all existing sessions for that user (via `session_service.invalidate_user_sessions()`).
   - Redirects to /login with a success message.

Email Service:
- For development, log verification/reset emails to the console (no real email sending).
- Structure the email-sending logic behind an abstraction (e.g., `EmailService` interface) so it can be swapped for a real provider (SES, SendGrid, etc.) in production.
- Store `FRONTEND_URL` as an environment variable (default: http://localhost:3000) used to construct verification/reset links.

Security Requirements:
- All tokens must be single-use (mark as consumed after use).
- Token secrets must come from environment variables, not hardcoded.
- Rate limit the register-request and password-reset-request endpoints (e.g., 5 requests per minute per IP).
- Do not reveal whether an email is registered in any response message.

New FastAPI Endpoints:
- POST /api/auth/register-request — accepts { email }, sends verification email.
- POST /api/auth/register-confirm — accepts { token, password }, creates user and session.
- POST /api/auth/password-reset-request — accepts { email }, sends reset email.
- POST /api/auth/password-reset-confirm — accepts { token, new_password }, resets password.

New Next.js Pages:
- /signup (app/(public)/signup/page.tsx) — email entry form.
- /signup/verify (app/(public)/signup/verify/page.tsx) — password creation form.
- /forgot-password (app/(public)/forgot-password/page.tsx) — email entry form.
- /forgot-password/reset (app/(public)/forgot-password/reset/page.tsx) — new password form.

Tests: Write tests for each new endpoint (register-request, register-confirm, password-reset-request, password-reset-confirm) covering happy path, expired tokens, duplicate emails, password mismatch, and rate limiting. Write component tests for the signup and forgot-password page forms.
