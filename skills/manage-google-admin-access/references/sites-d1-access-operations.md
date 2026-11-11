# Sites/D1 Google Access Operations

## Contents

1. Recommended architecture
2. Durable schema
3. Access Management API contract
4. Remove and disable semantics
5. Notification contract
6. UI behavior
7. Testing matrix
8. Sites deployment

## 1. Recommended architecture

Use direct Google OAuth only for identity and D1 for authorization state:

`Google identity → normalized email/domain → exact access_users lookup → hashed server session → role guard`

Keep login OAuth separate from Gmail/mailbox OAuth. A missing sender mailbox must not break site login.

## 2. Durable schema

Use equivalent tables:

- `access_users`: stable id, normalized unique email, display name, role, password hash only while a legacy fallback exists, created/updated/last-login timestamps.
- `access_sessions`: hashed token, user id, expiry, created time. Never store the raw cookie token.
- `google_access_states`: high-entropy state, PKCE verifier, safe return path, exact redirect URI, expiry, single-use lifecycle.
- `access_events`: actor id/email, target id/email/name, action, before/after role/name, timestamp. Do not use a foreign key that would erase the event when an allowlist user is removed.
- `access_notification_deliveries`: idempotency key, target, role, trigger, requester, status, provider id, safe error, timestamps.

Initialize D1 with one prepared SQL statement per table/index. Use `batch()` for multi-statement changes that must succeed together.

## 3. Access Management API contract

Protect every method with a server-side Owner check and `private, no-store` responses.

- `GET /api/admin/access-users`: list current allowlist users only.
- `POST`: validate exact company email and active role, create the allowlist user, append `grant`, then attempt notification after commit.
- `PATCH`: re-read the user, validate role, protect the last Owner, update role/name, revoke sessions, append `role-update`/`profile-update`, then optionally notify.
- `DELETE`: re-read the target, block self/last Owner, revoke sessions, append `remove`, and delete only the allowlist user.

Do not trust client-supplied email, current role, owner count, or actor identity. Derive them from the authenticated session and database.

For a grant/notification split response, use a shape such as:

```json
{
  "connected": true,
  "user": { "id": "...", "role": "editor" },
  "notification": { "sent": false, "error": "Provider unavailable" }
}
```

The HTTP response may still represent a successful grant; the UI must not claim the access transaction failed.

## 4. Remove and disable semantics

### Disable

Use when temporary suspension, restore, or retained identity is required. Keep the user row, set `role=disabled`, revoke sessions, and append an event.

### Remove

Use only after explicit user intent to remove the person from the product allowlist. Execute in one D1 batch where supported:

1. delete all `access_sessions` for the target;
2. insert an `access_events` snapshot with action `remove`;
3. delete the target `access_users` row.

Retain notification/event history. Never call Google Admin APIs, delete the Google account, or touch business records.

Required guards:

- target exists;
- actor is Owner;
- actor id is not target id;
- if target role is Owner, active Owner count remains at least one.

Re-granting the same email later creates a new allowlist identity and a new grant event.

## 5. Notification contract

Use a transactional provider with a verified company notification domain. Build the idempotency key from the immutable grant/role-change event, not from browser time alone.

The message contains:

- person's display name;
- assigned role;
- clean `/access` or production login URL;
- instruction to use Google;
- no password, code, OAuth state, or sender-mailbox secret.

Store `pending → sent/failed`. Retry only failed events; skip already-sent keys.

## 6. UI behavior

Recommended list columns: Person, Role, Last login, Actions.

- `Grant access`: one clear form; automatically notify on success when configured.
- `Save`: update role; do not email on an unchanged save.
- `Remove`: neutral-danger outline, not a primary button.
- Confirmation text: `This removes this application’s access and signs out existing sessions. The Google account is not deleted.`
- Current Owner row: show `Current account` instead of Remove.
- Success: name the person and state that only website access was removed.
- Failure: show the server error; do not remove the row optimistically unless rollback is reliable.

Do not keep bulk migration/reminder controls in the normal UI after the migration is complete. Keep backend delivery logs for audit.

## 7. Testing matrix

Unit/integration tests should cover:

- Owner can list, grant, change, disable/restore, and remove.
- Editor/Viewer receive 403 on every Access Management API method.
- domain-valid but unlisted Google user is denied.
- last Owner cannot be changed/disabled/removed.
- current Owner cannot remove self.
- removal deletes sessions and allowlist row, not Google/business data.
- removal appends a complete audit event.
- same email can be granted after removal.
- duplicate grant notification is idempotently skipped.
- notification failure does not roll back access.
- Access Management contains no permanent manual email control when automatic notification is the product rule.

Use fake/in-memory D1 for destructive test paths. Do not remove a real production person merely to verify code.

## 8. Sites deployment

- Keep the logical D1 binding in `.openai/hosting.json` and verify the real production binding exists.
- Runtime schema initialization may use `CREATE TABLE/INDEX IF NOT EXISTS`; committed migrations are preferable when the project already uses migration tooling.
- Build from the exact pushed commit. If the main worktree is dirty, package from a clean detached worktree.
- Save and deploy the same full commit SHA; do not guess or abbreviate the SHA for version creation.
- Verify the custom domain redirects unauthenticated `/access-management` requests to `/access`, then perform an authenticated Owner check.
