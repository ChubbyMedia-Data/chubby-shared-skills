#!/usr/bin/env python3
"""Audit a Next.js direct-Google-OAuth + Sites/D1 access implementation."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Check:
    level: str
    name: str
    detail: str


SKIP_PARTS = {
    ".git",
    ".next",
    ".vinext",
    "data",
    "dist",
    "node_modules",
    "tmp",
}


def read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def source_text(repo: Path, roots: tuple[str, ...]) -> str:
    chunks: list[str] = []
    for root_name in roots:
        root = repo / root_name
        if not root.exists():
            continue
        paths = [root] if root.is_file() else root.rglob("*")
        for path in paths:
            if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
                continue
            if path.suffix not in {".ts", ".tsx", ".js", ".jsx", ".sql", ".json"}:
                continue
            chunks.append(f"\n/* {path.relative_to(repo)} */\n{read(path)}")
    return "".join(chunks)


def add(
    checks: list[Check],
    ok: bool,
    name: str,
    failure: str,
    *,
    warning: bool = False,
) -> None:
    checks.append(Check("pass", name, "OK") if ok else Check("warn" if warning else "fail", name, failure))


def audit(repo: Path) -> list[Check]:
    checks: list[Check] = []
    package_text = read(repo / "package.json")
    try:
        package = json.loads(package_text) if package_text else {}
    except json.JSONDecodeError:
        package = {}
        checks.append(Check("fail", "package.json", "package.json is invalid JSON"))

    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    hosting_text = read(repo / ".openai/hosting.json")
    try:
        hosting = json.loads(hosting_text) if hosting_text else {}
    except json.JSONDecodeError:
        hosting = {}
        checks.append(Check("fail", "Sites metadata", ".openai/hosting.json is invalid JSON"))

    auth_text = source_text(
        repo,
        (
            "app/api/auth",
            "lib/google-site-auth.ts",
            "lib/site-access.ts",
            "worker/access-control.ts",
        ),
    )
    access_text = source_text(
        repo,
        (
            "app/api/admin",
            "app/access-management",
            "lib/access-pages.ts",
            "lib/site-access.ts",
            "worker/access-control.ts",
        ),
    )
    schema_text = source_text(repo, ("db", "worker/access-control.ts"))
    notification_text = source_text(
        repo,
        (
            "lib/access-notification-content.ts",
            "lib/access-notification-mail.ts",
            "lib/access-notification-provider.ts",
            "lib/resend-mail-client.ts",
            "app/api/admin/access-users",
        ),
    )
    tests_text = source_text(repo, ("tests",))
    env_example = read(repo / ".env.example")
    gitignore = read(repo / ".gitignore")

    add(checks, bool(package_text), "Next.js project", "package.json is missing")
    add(checks, "next" in dependencies, "Next.js dependency", "next dependency is missing")
    add(
        checks,
        bool(hosting.get("project_id")),
        "Existing Sites project",
        ".openai/hosting.json does not contain project_id",
    )
    add(
        checks,
        hosting.get("d1") not in (None, ""),
        "Sites D1 binding",
        ".openai/hosting.json does not declare a D1 binding",
    )

    identity_scope = re.search(r"openid[ ,]+email[ ,]+profile", auth_text, re.IGNORECASE)
    add(checks, identity_scope is not None, "Identity-only Google scopes", "Google OAuth does not clearly request openid email profile")
    add(
        checks,
        not re.search(r"gmail\.|mail\.google|/auth/gmail", auth_text, re.IGNORECASE),
        "No Gmail login scope",
        "Google login code appears to request Gmail/mail scopes; keep login identity-only",
    )
    add(checks, "email_verified" in auth_text, "Verified Google email", "OAuth callback does not clearly require email_verified")
    add(
        checks,
        any(marker in auth_text for marker in ("allowedDomain", "ALLOWED_DOMAIN", "allowed_domain")),
        "Company-domain validation",
        "No explicit allowed company-domain validation was found",
    )
    add(
        checks,
        any(marker in auth_text for marker in ("findAccessUserByEmail", "access_users", "allowlist")),
        "Exact allowlist authorization",
        "No exact server-side access-user lookup was found",
    )
    add(checks, "state" in auth_text and "code_verifier" in schema_text, "OAuth state and PKCE", "OAuth state/PKCE persistence is incomplete")
    add(
        checks,
        all(marker in auth_text for marker in ("HttpOnly", "SameSite=Lax")),
        "Secure session-cookie contract",
        "Session cookie does not clearly use HttpOnly and SameSite=Lax",
    )

    for table in ("access_users", "access_sessions", "google_access_states", "access_events"):
        add(checks, table in schema_text, f"D1 table: {table}", f"D1 schema does not define {table}")
    add(
        checks,
        "access_notification_deliveries" in schema_text,
        "Notification delivery history",
        "No durable access-notification delivery table was found",
        warning=True,
    )

    add(
        checks,
        re.search(r"role\s*!==\s*[\"']owner[\"']", access_text) is not None,
        "Owner-only Access Management API",
        "Access-management server routes do not clearly reject non-Owners",
    )
    add(checks, "listAccessUsers" in access_text, "Access list", "No protected user-list operation was found")
    add(checks, "createAccessUser" in access_text, "Grant access", "No grant-access operation was found")
    add(checks, "updateAccessUser" in access_text, "Role updates", "No role-update operation was found")
    add(checks, "removeAccessUser" in access_text and "DELETE" in access_text, "Remove access", "No protected remove-access operation was found")
    add(
        checks,
        "cannot remove your own" in access_text.lower(),
        "Self-removal guard",
        "Remove does not clearly block the signed-in Owner from removing self",
    )
    add(
        checks,
        "last Owner" in access_text,
        "Last-Owner guard",
        "No last-Owner demotion/removal protection was found",
    )
    add(
        checks,
        "DELETE FROM access_sessions" in access_text,
        "Session revocation",
        "Role change/removal does not clearly revoke existing sessions",
    )
    add(
        checks,
        "INSERT INTO access_events" in access_text and "'remove'" in access_text,
        "Append-only access audit",
        "Permission operations do not clearly append access events",
    )
    add(
        checks,
        "Google account is not deleted" in access_text,
        "Remove semantics explained",
        "Remove confirmation does not explain that the Google account remains",
        warning=True,
    )
    add(
        checks,
        "currentUserId" in access_text and "Current account" in access_text,
        "Current Owner UI protection",
        "Access Management does not hide/replace Remove for the current account",
        warning=True,
    )

    add(
        checks,
        "sendAccessInvitationOnce" in notification_text,
        "Automatic access notification",
        "Grant flow does not clearly attempt an automatic notification",
        warning=True,
    )
    add(
        checks,
        "idempotency" in notification_text.lower(),
        "Idempotent notification",
        "Notification flow has no clear idempotency key/history",
        warning=True,
    )
    add(
        checks,
        "notification?.sent" in access_text or "notification.sent" in access_text,
        "Split grant/delivery result",
        "UI does not clearly distinguish access success from email delivery failure",
        warning=True,
    )
    add(
        checks,
        "Send current users once" not in access_text,
        "No permanent bulk reminder UI",
        "A one-time bulk reminder control is still visible in normal Access Management",
        warning=True,
    )

    add(
        checks,
        any(marker in tests_text for marker in ("Google access", "Google authorization", "google-site-auth")),
        "Focused Google OAuth tests",
        "No focused Google OAuth test was found",
        warning=True,
    )
    add(
        checks,
        "last Owner cannot be removed" in tests_text and "cannot remove their own" in tests_text,
        "Removal safety tests",
        "No focused tests for self-removal and last-Owner protection were found",
        warning=True,
    )
    add(
        checks,
        "Viewer" in tests_text or "viewer" in tests_text,
        "Role behavior tests",
        "No test evidence for Viewer/Editor authorization behavior was found",
        warning=True,
    )

    secret_names = ("SITE_GOOGLE_CLIENT_ID", "SITE_GOOGLE_CLIENT_SECRET", "SITE_SESSION_SECRET")
    add(
        checks,
        any(name in env_example for name in secret_names),
        "Environment placeholders",
        ".env.example does not document Google/session configuration",
        warning=True,
    )
    add(
        checks,
        ".env" in gitignore,
        "Secret file ignore rule",
        ".gitignore does not appear to ignore environment files",
    )
    local_envs = [path.name for path in repo.glob(".env*") if path.name != ".env.example"]
    add(
        checks,
        not local_envs,
        "Local secrets review",
        f"Review local secret-bearing files without printing them: {', '.join(sorted(local_envs))}",
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
        print(json.dumps({"repo": str(repo), "checks": [asdict(check) for check in checks]}, ensure_ascii=False, indent=2))
    else:
        labels = {"pass": "PASS", "warn": "WARN", "fail": "FAIL"}
        for check in checks:
            print(f"[{labels[check.level]}] {check.name}: {check.detail}")
        totals = {level: sum(check.level == level for check in checks) for level in ("pass", "warn", "fail")}
        print(f"\nSummary: {totals['pass']} passed, {totals['warn']} warnings, {totals['fail']} failed")
    return 1 if any(check.level == "fail" for check in checks) or (args.strict and any(check.level == "warn" for check in checks)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
