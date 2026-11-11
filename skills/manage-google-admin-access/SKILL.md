---
name: manage-google-admin-access
description: Build, audit, repair, deploy, or operate Google company-account login and server-side Owner/Editor/Viewer access control for Next.js websites using direct Google OAuth or Neon Auth with durable Sites/Cloudflare D1, Neon, Postgres, or Vercel storage. Use when replacing shared access codes, restricting a site to approved company Google accounts, creating Access Management, granting/changing/disabling/removing/restoring users, sending automatic access notifications, protecting the last Owner, adding permission audit history, or diagnosing callbacks, login loops, access denial, session, database, and deployment failures. This skill does not implement Gmail mailbox authorization, business-email composition, or general email sending.
---

# Manage Google Admin Access

Use Google only to verify identity. Resolve product access from a durable server-side allowlist and role store. Never grant access from a company-domain match alone.

## Portability and authorization

This skill uses the standard SKILL.md format and can be installed in Claude or Codex. Tool names in examples describe capabilities; discover the equivalent authorized tools in the current environment. Installing this skill grants no credentials or account permissions. If a provider connector is unavailable, use its official CLI or an authorized browser session where supported; otherwise explain the exact manual step. Do not bypass access controls. For a domain outside Chubby Media, use only the domain explicitly authorized by the user.

## Keep the scope exact

Cover:

- Google OAuth identity verification with `openid email profile`
- Owner / Editor / Viewer / Disabled authorization
- durable sessions, OAuth state, access users, and permission events
- Owner-only Access Management
- grant, role change, disable, restore, and safe removal
- optional one-way access notification after a committed grant/change
- deployment and production verification

Do not request Gmail scopes, connect a sender mailbox, manage Google Workspace accounts, or build a general email composer. Removing website access must never delete the person's Google account.

## Choose the operation

- **Add integration**: build Google login, role storage, sessions, server guards, Access Management, migration, and rollback.
- **Audit or repair**: inspect the live flow and diagnose callbacks, loops, denied accounts, stale roles, missing storage, or deployment drift.
- **Operate access**: grant, change, disable, restore, or remove an exact user after reading current live state.
- **Add notification**: automatically notify a person after access commits, without adding Gmail login scopes.
- **Harden governance**: add last-Owner protection, self-removal protection, session revocation, audit events, and Owner-only server enforcement.

## Inspect before changing anything

1. Locate the exact repository, branch, dirty state, production URL, hosting project, database, callback URL, and rollback path.
2. Read auth routes, session helpers, access middleware, permission APIs, Access Management UI, schema/migrations, tests, `.env.example`, `.gitignore`, and hosting metadata.
3. Identify the implementation:
   - direct Google OAuth + SQL role store;
   - Neon Auth + application role store;
   - temporary dual-login migration.
4. Read the live permission list before mutating it. Confirm the exact email, requested role, and whether the user asked to disable or fully remove access.
5. Preserve unrelated working-tree changes and existing access. Never use a permission change as a test unless the exact account/action is authorized.

## Read the matching implementation reference

- Direct Google OAuth: read `references/google-oauth-rbac-pattern.md`.
- Sites/Cloudflare + D1 Access Management: also read `references/sites-d1-access-operations.md`.
- Next.js + Neon Auth: read `references/nextjs-neon-pattern.md`.

Do not mix callback/session mechanisms from different providers.

## Enforce the security contract

- Request only `openid email profile` for login.
- Verify OAuth state, exact callback origin, issuer, audience, expiry, verified email, allowed company domain, and exact allowlist record.
- Store OAuth state, hashed sessions, users, roles, and append-only access events in durable server storage.
- Store secrets only in hosted secret configuration. Never place them in frontend code, readable cookies, Lark business tables, localStorage, Git, terminal reports, or chat.
- Use HttpOnly, Secure, SameSite=Lax cookies in production and invalidate sessions after role change, disable, or removal.
- Fail closed when OAuth, session, or role storage is unavailable.
- Enforce roles in every protected server route. UI hiding is not authorization.
- Return private auth/admin responses with `Cache-Control: private, no-store`.
- Never expose tokens, access codes, sessions, provider credentials, or unrelated users.

## Apply the role and lifecycle rules

- **Owner**: full product access and Access Management.
- **Editor**: normal product writes; no Access Management.
- **Viewer**: read/export only; server rejects writes.
- **Disabled**: identity is retained but product access is denied.

For every grant, role change, disable, restore, Owner binding, and removal, append an event with actor, target, before/after state, action, and time.

Always protect:

- the final active Owner from demotion, disablement, or removal;
- the current Owner from accidentally removing their own access;
- all active sessions for a user whose role is changed, disabled, or removed.

Choose **Disabled** when reversible suspension or compliance history is the product requirement. Choose **Remove** only when the user explicitly wants the person gone from the website allowlist. A safe Remove must:

1. re-read the target server-side;
2. verify the actor is Owner;
3. block self-removal and last-Owner removal;
4. write an immutable audit event;
5. delete/revoke website sessions;
6. remove only the application allowlist row;
7. preserve Google Workspace, notification logs, business data, and unrelated systems;
8. allow the email to be granted again later.

## Build Access Management as a product flow

- Show the page and navigation only to Owner, and independently return 403 from its APIs for Editor/Viewer.
- List name, company email, role, and last login.
- Add an exact company email and selected role.
- Change roles only through a protected server action.
- Provide either Disabled/Restore or a clearly labeled Remove flow according to the requested semantics.
- Use an explicit confirmation dialog for Remove. State that only website access is removed and the Google account remains.
- Hide the Remove control for the signed-in Owner and still enforce the guard server-side.
- Do not leave bootstrap `Claim Owner` controls visible after a real Owner is bound.
- Avoid duplicate actions. If granting access automatically sends a notification, do not add a second permanent `Send email` button.
- Do not leave one-time migration/reminder controls on the normal page after they are no longer operationally useful.
- Report split outcomes accurately: access may succeed even when notification delivery fails.

## Send access notifications safely

- Send only after the access transaction commits.
- Default to one notification for a new grant. Send role-change notices only when product policy requires it.
- Use a separate transactional provider such as Resend; never add Gmail scopes to login.
- Include recipient name, role, clean production login URL, and support contact. Never include a password, access code, OAuth state URL, or secret.
- Make delivery idempotent per grant/change event and store safe delivery status plus provider message ID.
- Do not roll back access when delivery fails. Return `Access granted · email not sent` and expose a narrowly scoped retry only when needed.
- Never send a real notification in tests without explicit approval for the exact recipient and content.

## Migrate from shared access codes safely

1. Add Google login and durable role storage while keeping the existing gate as rollback.
2. Bind and verify at least one real Owner company account.
3. Add approved Editors/Viewers and verify their real server permissions.
4. Verify an unlisted same-domain account is denied.
5. Retire the shared code only after Google login, Owner recovery, and rollback are proven.
6. Remove temporary Owner-claim UI after binding and time-bound any dual-login period.

## Validate before claiming completion

Run the matching static audit:

- Sites/D1 direct OAuth: `python3 scripts/audit_nextjs_d1_google_access.py <repo>`
- Neon Auth: `python3 scripts/audit_nextjs_google_admin.py <repo>`

Then verify:

1. focused auth/access tests, typecheck, production build, schema/migration checks, and diff checks pass;
2. the exact validated source is committed and deployed to the existing project/domain;
3. a real Owner completes Google selection → callback → clean product URL;
4. Owner sees Access Management; Editor/Viewer do not and their direct API calls return 403;
5. Editor writes succeed, Viewer writes fail, and Disabled/unlisted users are denied;
6. Grant persists and the automatic notification reports sent/failed separately;
7. role changes persist and revoke old sessions;
8. Remove affects only website access, blocks self/last Owner, and permits later re-grant;
9. audit events exist for all successful permission changes;
10. no Gmail scope, sender-mailbox authorization, or general email composer was introduced.

When the intended Google account is clear and the work is already authorized, handle ordinary account selection, account switching, sign-in, and routine admin-console configuration directly. Do not hand these steps back to the user or request repeated permission merely because they involve Google account selection. Ask for clarification only when the intended account or required recipient cannot be established from context. Follow any higher-priority tool requirements for user-only verification, credentials, CAPTCHA, or action-time approval; hand off only the specific step that requires the user, then resume the remaining work. Sending notifications still requires authorization and a verified recipient. Never call a static audit or successful deployment proof of a working live login.

## Publish without mixing unrelated work

On an existing Sites project, preserve `.openai/hosting.json` and its project ID. When the shared worktree contains unrelated changes:

1. stage and commit only the access-control files;
2. push that exact commit;
3. create a clean detached worktree from the pushed commit;
4. run tests/build and package the site from that clean source;
5. save/deploy the version using the exact full commit SHA;
6. confirm deployment success and the custom-domain auth redirect.

Do not add untracked data, temp output, local environment files, or secrets.

## Report the result

Lead with what is actually working. State the provider, production URL/path, durable role store, supported roles/actions, real callback result, permission tests, notification result, deployment/version, and any remaining user action. Never reveal secrets, access codes, OAuth parameters, session values, or unrelated member data.
