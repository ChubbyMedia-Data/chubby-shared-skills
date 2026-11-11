#!/usr/bin/env python3
"""Audit a Next.js + Neon Auth Google admin-access implementation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class Check:
    level: str
    name: str
    detail: str


def read(repo: Path, relative: str) -> str:
    path = repo / relative
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def exists(repo: Path, relative: str) -> bool:
    return (repo / relative).is_file()


def add(checks: list[Check], ok: bool, name: str, failure: str, warning: bool = False) -> None:
    if ok:
        checks.append(Check("pass", name, "OK"))
    else:
        checks.append(Check("warn" if warning else "fail", name, failure))


def audit(repo: Path) -> list[Check]:
    checks: list[Check] = []
    package_text = read(repo, "package.json")
    try:
        package = json.loads(package_text) if package_text else {}
    except json.JSONDecodeError:
        package = {}
        checks.append(Check("fail", "package.json", "package.json is invalid JSON"))

    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    add(checks, bool(package_text), "Next.js project", "package.json is missing")
    add(checks, "next" in dependencies, "Next.js dependency", "next dependency is missing")
    add(
        checks,
        "@neondatabase/auth" in dependencies,
        "Neon Auth dependency",
        "@neondatabase/auth dependency is missing",
    )

    server_auth = read(repo, "lib/auth/server.ts")
    client_auth = read(repo, "lib/auth/client.ts")
    handler = read(repo, "app/api/auth/[...path]/route.ts")
    admin_page = read(repo, "app/admin/page.tsx")
    proxy = read(repo, "proxy.ts") or read(repo, "middleware.ts")
    fallback = read(repo, "app/auth/sign-in/page.tsx")
    access = read(repo, "lib/admin-access.ts")
    auth_route = read(repo, "app/api/admin/auth/route.ts")
    schema = read(repo, "db/schema.ts")
    managers = read(repo, "app/api/admin/managers/route.ts")
    manager_delete = read(repo, "app/api/admin/managers/[email]/route.ts")
    env_example = read(repo, ".env.example")
    gitignore = read(repo, ".gitignore")
    drizzle_config = read(repo, "drizzle.config.ts") or read(repo, "drizzle.config.js")

    add(checks, "createNeonAuth" in server_auth, "Server auth singleton", "lib/auth/server.ts does not create Neon Auth")
    add(
        checks,
        bool(re.search(r"sameSite\s*:\s*[\"']lax[\"']", server_auth)),
        "OAuth return cookie",
        'Set cookies.sameSite to "lax" so the Google top-level return includes the challenge cookie',
    )
    add(
        checks,
        re.search(r"NEON_AUTH_COOKIE_SECRET\s*(?:\|\||\?\?)", server_auth) is None,
        "Production cookie secret fails closed",
        "NEON_AUTH_COOKIE_SECRET has a code fallback; ensure production throws when it is missing",
        warning=True,
    )
    add(
        checks,
        re.search(r"NEON_AUTH_BASE_URL\s*(?:\|\||\?\?)", server_auth) is None,
        "Production auth base URL fails closed",
        "NEON_AUTH_BASE_URL has a code fallback; ensure production throws when it is missing",
        warning=True,
    )
    add(checks, "createAuthClient" in client_auth, "Client auth", "lib/auth/client.ts does not create the auth client")
    add(checks, "auth.handler()" in handler, "Auth API handler", "app/api/auth/[...path]/route.ts does not expose auth.handler()")
    add(
        checks,
        "signIn.social" in admin_page and re.search(r"provider\s*:\s*[\"']google[\"']", admin_page) is not None,
        "Google sign-in",
        "Admin page does not call signIn.social with provider google",
    )
    add(
        checks,
        re.search(r"callbackURL\s*:\s*[\"']/admin[\"']", admin_page) is not None,
        "Admin callback",
        'Google sign-in callbackURL should point to "/admin"',
    )
    add(checks, bool(proxy), "Proxy or middleware", "No proxy.ts or middleware.ts was found")
    add(
        checks,
        "neon_auth_session_verifier" in proxy,
        "Verifier exchange trigger",
        "Proxy/middleware does not detect neon_auth_session_verifier",
    )
    add(
        checks,
        re.search(r"loginUrl\s*:\s*[\"']/auth/sign-in[\"']", proxy) is not None,
        "Separate login fallback",
        'Use loginUrl "/auth/sign-in"; do not use "/admin" because it can bypass verifier processing',
    )
    add(
        checks,
        "/admin" in proxy and "matcher" in proxy,
        "Admin proxy matcher",
        "Proxy/middleware matcher does not clearly cover /admin",
    )
    add(
        checks,
        bool(fallback) and "redirect" in fallback and "/admin" in fallback,
        "Fallback sign-in route",
        "app/auth/sign-in/page.tsx should redirect to /admin to avoid a 404",
    )

    add(checks, "auth.getSession" in access, "Server session lookup", "Authorization helper does not read the server session")
    add(
        checks,
        "toLowerCase" in access and "trim" in access,
        "Email normalization",
        "Normalize admin emails with trim and lowercase",
    )
    add(
        checks,
        "getAdminAuthorization" in auth_route,
        "Admin auth endpoint",
        "Admin auth endpoint does not call the shared authorization helper",
    )
    add(
        checks,
        "no-store" in auth_route,
        "Private auth caching",
        "Admin auth response should use private/no-store caching",
    )
    add(
        checks,
        "adminUsers" in schema or "admin_users" in schema,
        "Admin permission table",
        "Database schema does not define an admin permission table",
    )
    add(
        checks,
        "disabled" in schema,
        "Reversible admin removal",
        "Admin table should preserve disabled state instead of hard-deleting audit history",
        warning=True,
    )
    add(
        checks,
        "getAdminAuthorization" in managers,
        "Protected manager writes",
        "Admin manager API is not protected by the shared authorization helper",
    )
    add(
        checks,
        "ADMIN_OWNER_EMAILS" in manager_delete and ("不能删除" in manager_delete or "includes(email)" in manager_delete),
        "Owner deletion guard",
        "Delete endpoint does not clearly prevent Owner removal",
    )
    owner_only_management = all(
        "authorization.role" in source and "owner" in source
        for source in (managers, manager_delete)
    )
    add(
        checks,
        owner_only_management,
        "Access-management role policy",
        "Admin-management endpoints do not appear Owner-only; confirm delegated Admin governance is intentional",
        warning=True,
    )
    domain_policy_text = "\n".join((access, auth_route, managers, manager_delete, env_example))
    add(
        checks,
        "ADMIN_ALLOWED_DOMAINS" in domain_policy_text or "endsWith" in domain_policy_text,
        "Company-domain policy",
        "No explicit company-domain restriction found; exact allowlisting may still permit external Admins",
        warning=True,
    )
    initial_admin_runtime = "ADMIN_INITIAL_EMAILS" in "\n".join((access, auth_route, managers, manager_delete))
    add(
        checks,
        not initial_admin_runtime,
        "Bootstrap Admin retirement",
        "ADMIN_INITIAL_EMAILS remains a runtime authorization source; define and execute a retirement plan",
        warning=True,
    )
    audit_history_text = "\n".join((schema, managers, manager_delete))
    add(
        checks,
        ("adminAccessEvents" in audit_history_text or "admin_access_events" in audit_history_text)
        and "action" in audit_history_text
        and "createdAt" in audit_history_text,
        "Permission event history",
        "No append-only Admin permission event table was found; current-state fields are not a full audit trail",
        warning=True,
    )

    migration_files = [
        path
        for root in (repo / "drizzle", repo / "migrations")
        if root.is_dir()
        for path in root.rglob("*.sql")
    ]
    migration_text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in migration_files)
    postgres_configured = bool(re.search(r"dialect\s*:\s*[\"']postgresql[\"']", drizzle_config))
    sqlite_markers = "`" in migration_text or re.search(r"\bAUTOINCREMENT\b", migration_text, re.IGNORECASE) is not None
    add(
        checks,
        not (postgres_configured and sqlite_markers),
        "Migration dialect matches database",
        "PostgreSQL is configured but committed SQL contains SQLite-style syntax; regenerate and test clean migrations",
        warning=True,
    )

    test_script = str(package.get("scripts", {}).get("test", ""))
    auth_test_texts: list[str] = []
    for pattern in ("*.test.ts", "*.test.tsx", "*.spec.ts", "*.spec.tsx", "*.test.js", "*.spec.js"):
        for path in repo.rglob(pattern):
            if "node_modules" in path.parts or ".next" in path.parts:
                continue
            auth_test_texts.append(path.read_text(encoding="utf-8", errors="replace"))
    auth_tests = "\n".join(auth_test_texts)
    add(
        checks,
        bool(auth_tests) and any(
            marker in auth_tests
            for marker in ("neon_auth_session_verifier", "getAdminAuthorization", "signIn.social", "Unauthorized")
        ),
        "Focused auth and authorization tests",
        f"No focused OAuth/authorization tests found; current test command is: {test_script or '(missing)'}",
        warning=True,
    )

    for key in ("NEON_AUTH_BASE_URL", "NEON_AUTH_COOKIE_SECRET", "ADMIN_OWNER_EMAILS"):
        add(checks, key in env_example, f"Environment placeholder: {key}", f".env.example is missing {key}")
    add(
        checks,
        ".env*" in gitignore or ".env" in gitignore,
        "Secret file ignore rule",
        ".gitignore does not ignore environment files",
    )

    tracked_envs = [p.name for p in repo.glob(".env*") if p.name != ".env.example"]
    add(
        checks,
        not tracked_envs,
        "No local environment files in target",
        f"Review possible secret-bearing files: {', '.join(sorted(tracked_envs))}",
        warning=True,
    )
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", nargs="?", default=".", help="Path to the Next.js repository")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    parser.add_argument("--strict", action="store_true", help="Return nonzero when warnings are present")
    args = parser.parse_args()
    repo = Path(args.repo).expanduser().resolve()
    if not repo.is_dir():
        print(f"Repository path does not exist: {repo}", file=sys.stderr)
        return 2

    checks = audit(repo)
    if args.json:
        print(json.dumps({"repo": str(repo), "checks": [asdict(c) for c in checks]}, ensure_ascii=False, indent=2))
    else:
        labels = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
        for check in checks:
            print(f"[{labels[check.level]}] {check.name}: {check.detail}")
        totals = {level: sum(c.level == level for c in checks) for level in ("pass", "warn", "fail")}
        print(f"\nSummary: {totals['pass']} passed, {totals['warn']} warnings, {totals['fail']} failed")
    return 1 if any(c.level == "fail" for c in checks) or (args.strict and any(c.level == "warn" for c in checks)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
