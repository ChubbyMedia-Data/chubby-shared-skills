# Next.js + Neon Auth + Google Admin Pattern

## Contents

1. Architecture
2. Required files
3. Environment and provider settings
4. Permission rules
5. Troubleshooting
6. Acceptance checklist

## 1. Architecture

Use Google only to prove identity. Use the application database and protected environment settings to decide authorization.

Flow:

`Admin page → Google OAuth → /admin?neon_auth_session_verifier=... → server verifier exchange → session cookie → server allowlist check → admin console or access denied`

Do not rely on a hidden admin URL, client-side email comparison, or a shared access code.

## 2. Required files

### Server auth singleton

```ts
import { createNeonAuth } from "@neondatabase/auth/next/server";

export const auth = createNeonAuth({
  baseUrl: process.env.NEON_AUTH_BASE_URL!,
  cookies: {
    secret: process.env.NEON_AUTH_COOKIE_SECRET!,
    sessionDataTtl: 300,
    sameSite: "lax",
  },
});
```

Use a placeholder only for an explicitly detected local build-time evaluation when the framework requires it. In production, throw a configuration error when the base URL or cookie secret is missing. Never let a known fallback become the production signing secret.

### Auth API handler

`app/api/auth/[...path]/route.ts`:

```ts
import { auth } from "../../../../lib/auth/server";

export const dynamic = "force-dynamic";
export const { GET, POST, PUT, DELETE, PATCH } = auth.handler();
```

### Client login

```ts
const result = await authClient.signIn.social({
  provider: "google",
  callbackURL: "/admin",
});
```

### Next.js 16 proxy

```ts
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";
import { auth } from "./lib/auth/server";

const neonAuthMiddleware = auth.middleware({ loginUrl: "/auth/sign-in" });

export function proxy(request: NextRequest) {
  if (!request.nextUrl.searchParams.has("neon_auth_session_verifier")) {
    return NextResponse.next();
  }
  return neonAuthMiddleware(request);
}

export const config = { matcher: ["/admin"] };
```

Do not set `loginUrl: "/admin"`. Neon Auth treats the login URL as an allowed route and can skip verifier processing on the callback itself.

### Fallback login page

`app/auth/sign-in/page.tsx`:

```ts
import { redirect } from "next/navigation";

export default function SignInFallback() {
  redirect("/admin");
}
```

This prevents a missing `/auth/sign-in` route from becoming a 404 while keeping it distinct from the OAuth callback path.

### Server authorization

Normalize the session email with `trim().toLowerCase()`. Check immutable Owners first, then active Admin database records, then any temporary bootstrap list. Return both signed-in status and allowed role so the UI can distinguish login failure from access denial.

Every admin data route must call the same server authorization helper before reading or writing data.

## 3. Environment and provider settings

Required environment names commonly include:

- `DATABASE_URL`
- `NEON_AUTH_BASE_URL`
- `NEON_AUTH_COOKIE_SECRET` with at least 32 random characters
- `ADMIN_OWNER_EMAILS`
- optional `ADMIN_INITIAL_EMAILS`

If `ADMIN_INITIAL_EMAILS` is used to bootstrap a migration, migrate those accounts into the live permission store and then retire or explicitly time-bound the bootstrap path.

In Neon Auth:

- enable Google as a social provider;
- add the exact production origin as trusted;
- keep email/password sign-in disabled when the product is Google-only.

In Vercel:

- define required variables for Production and relevant Preview environments;
- redeploy after variable changes;
- verify the custom domain points to the same project being deployed.

Never put secret values in committed files, skill resources, terminal output, or user-facing reports.

## 4. Permission rules

- Owners come from protected configuration and cannot be removed through normal Admin endpoints.
- Admin records use a primary key email plus `created_at`, `created_by`, and `disabled` or equivalent state.
- Adding an existing disabled Admin restores it and updates the actor.
- Removing an Admin disables the record instead of erasing the audit trail.
- The UI may list roles, but the API is the authority.
- If company-domain-only access is required, validate both the domain and the allowlist. Domain matching alone grants too much access.
- Default access-management endpoints to Owner-only. Delegate access management to Admins only after an explicit policy decision.
- When historical accountability is required, append an event for every grant, restore, disable, role change, and Owner configuration change. A mutable current-state row is not an audit log.
- Keep schema tooling and committed migrations on the same database dialect as production; validate a clean migration, not only an existing database connection.

## 5. Troubleshooting

### `/auth/sign-in` is 404

The auth middleware used its default fallback, but the app lacks that route. Add the redirect page; do not change the callback path to the login path.

### Google returns to the login page with a verifier still in the URL

Check, in order:

1. The production request is reaching `proxy.ts` or the correct middleware file.
2. The matcher covers `/admin`.
3. The code invokes Neon middleware when `neon_auth_session_verifier` is present.
4. `loginUrl` is not `/admin`.
5. Server cookie configuration uses `sameSite: "lax"`.
6. The callback's challenge cookie has not expired and the trusted origin is exact.

### Login works only after refresh

This strongly suggests a cross-site return-cookie problem. `SameSite=Strict` can omit the challenge cookie on the first top-level return from Google; a same-site refresh may then work. Use `sameSite: "lax"` and repeat a fresh login flow.

### `Invalid origin`

Add the exact scheme and host, such as `https://admin.example.com`, to the auth provider's trusted origins. Check Preview and Production separately.

### Signed in but no permission

Show the normalized session email. Check it against the live Owner/Admin state. Do not silently add it or weaken the allowlist.

### Deployment succeeds but behavior is unchanged

Verify the production custom domain is attached to the deployed project and commit. Check deployment status, environment scope, and browser network/DOM state. Avoid assuming that a Git push means production has switched.

### Static audit passes but production is not ready

Static text checks cannot prove live provider configuration, environment scope, permission policy, clean migrations, or browser session behavior. Review warnings, run focused tests, deploy, and complete the real browser acceptance flow.

## 6. Acceptance checklist

- Google account selection completes.
- Callback verifier disappears.
- Final URL is clean `/admin`.
- Session email matches the chosen account.
- Allowed Owner/Admin sees the console.
- Unlisted user sees access denied and no admin data.
- Owner cannot be removed through UI or API.
- Admin add/disable persists after reload.
- Only the role chosen by policy can manage Admin access.
- Company-domain policy is explicit and tested.
- Permission changes have the required event history.
- A clean production-dialect database migration succeeds.
- Focused OAuth and authorization tests run in addition to lint/build.
- Auth and admin API responses are not publicly cached.
- No password fallback or access code remains when Google-only login was requested.
