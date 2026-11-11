# Direct Google OAuth + SQL RBAC Pattern

## Contents

1. Architecture
2. Data model
3. OAuth and session flow
4. Authorization contract
5. Access Management
6. Hosting and deployment
7. Acceptance checklist

## 1. Architecture

Use Google only for identity. Resolve product permissions from a durable SQL role store.

`Login → Google OAuth (openid email profile) → callback validates state/code/email → server session → role lookup → product or access denied`

Use this pattern for a custom Next.js OAuth implementation on Sites/Cloudflare/D1, Vercel/Postgres, or a compatible server runtime. Do not add Gmail scopes. An optional access-grant notification uses a separate server-side delivery provider.

## 2. Data model

Use equivalent durable tables for:

- `access_users`: id, normalized email, display name, role, active/disabled state, Google subject, created/updated actor and timestamps, last login.
- `access_sessions`: hashed session token, user id, expiry, created/last-used timestamps.
- `oauth_states`: hashed/random state, return path, mode, expiry, single-use timestamp.
- `access_events`: actor, target, action, before/after role, timestamp, optional reason.
- optional `access_notifications`: access event id, recipient, template version, provider message id, delivery state, attempt count, timestamps, and last safe error code.

Never store raw session tokens. Never use a business Lark Base as an OAuth token/session store.

## 3. OAuth and session flow

1. Generate a high-entropy, short-lived, single-use `state` server-side.
2. Store only a validated relative return path.
3. Redirect to Google with exact callback URI and scopes `openid email profile`.
4. Exchange the authorization code server-side.
5. Verify issuer, audience/client id, expiry, nonce/state, `email_verified`, normalized email, and approved company domain.
6. Look up the exact user role; do not auto-create access merely because the domain matches.
7. Create a random session, store only its hash, and set an HttpOnly/Secure/SameSite=Lax cookie.
8. Redirect to a clean URL without verifier/code/state parameters.

Keep login OAuth credentials separate from any future Gmail/mail credentials. Login must continue working when mail features are absent.

## 4. Authorization contract

Centralize role resolution in one server helper and use it in every protected page/API.

- Owner: product writes plus Access Management.
- Editor: product writes only.
- Viewer: read/export only.
- Disabled/unlisted: no product data.

Return 401 for no valid session and 403 for a signed-in user lacking the required role. UI visibility must mirror, not replace, server authorization.

Prevent the last active Owner from being disabled or demoted. Normalize all emails with `trim().toLowerCase()`.

## 5. Access Management

Show the page/link only to Owner, and independently protect the route and APIs server-side.

Support:

- add an exact company Google email;
- set Owner/Editor/Viewer/Disabled;
- restore a disabled account;
- view last login and role-change history.

An Owner-claim link is a migration/bootstrap control, not a permanent primary action. Display it only when the current legacy Owner session has no bound Google identity; hide it after successful binding.

If access notification is enabled, send it only after the grant commits. Make it idempotent by access-event id, report grant and delivery separately, and offer Owner-only retry. The message may contain the assigned role and clean production login URL, but never a password, access code, OAuth state URL, or secret. Do not add Gmail scopes or business-mail composition.

## 6. Hosting and deployment

- Use the platform's durable production database/binding, not filesystem memory.
- Configure the exact production callback URL and authorized JavaScript origin in Google Cloud.
- Keep client id, client secret, session secret, and database credentials in platform secrets.
- Apply migrations before enabling Google-only access.
- Redeploy after environment/OAuth callback changes.
- Keep the current login method as rollback until a real Owner Google login succeeds.

For Cloudflare/D1 or Sites D1, verify bindings exist in the production runtime, not only local config. For Postgres/Neon, verify connection pooling and migration dialect.

## 7. Acceptance checklist

- Only `openid email profile` scopes are requested.
- A real approved Owner completes Google login.
- Callback parameters disappear from the final URL.
- The role persists after reload and a new browser session.
- Owner can manage access; Editor/Viewer cannot see or call management APIs.
- Editor write succeeds; Viewer write returns 403.
- Unlisted same-domain user is denied.
- Disabled user is denied.
- Last Owner cannot be demoted.
- Every access change creates an immutable event.
- Private responses use no-store caching.
- Logout invalidates the session.
- No Gmail login scopes, sender-mailbox connection, or general mail composer was added.
- If access notification is enabled, duplicate requests do not send duplicate messages and a delivery failure does not undo the role grant.
