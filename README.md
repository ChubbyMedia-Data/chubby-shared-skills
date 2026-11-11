# Chubby shared skills

Public, portable copies of two Chubby Media workflows. No credentials, production account IDs, customer data, or provider permissions are included. The existing private plugin repository is unchanged.

## Skills

- [Chubby Domain Manager](skills/chubby-domain-manager/SKILL.md): connect and verify custom domains with Cloudflare, Vercel, or ChatGPT Sites.
- [Manage Google Admin Access](skills/manage-google-admin-access/SKILL.md): Google sign-in and server-side access management.

## Claude chat / Desktop

Download each ZIP from [Releases](https://github.com/ChubbyMedia-Data/chubby-shared-skills/releases/latest), then upload it in Claude’s Skills settings and enable it. Depending on the UI version this appears under Customize → Skills or Settings → Capabilities. Organization policy may restrict custom skills. Uploading these files to GitHub does not automatically install them in Claude or make every conversation search this repository.

## Claude Code

Copy an individual skill directory into `~/.claude/skills/` for personal use or `.claude/skills/` in a project. Keep SKILL.md and its references/scripts together.

## Codex

Install an individual skill directory into your configured skills directory, such as `~/.codex/skills/`, and start a new session. This repository contains skill folders, not a Codex plugin marketplace. Ordinary ChatGPT conversations do not automatically load local Codex skills.

## Operational limits

Skills provide instructions, not account access. Claude or Codex must separately have the relevant authorized connectors, CLI, browser capabilities, and deployment permissions. Sites-specific steps require a Sites-capable environment. Static audit scripts are heuristics, not proof of working authentication or a security certification. Check current provider documentation and perform live verification.

## Source and updates

Published from the local Chubby skill copies on 2026-11-10 with a portability note. These are versioned snapshots, not an automatic sync with the private repository. Review diffs before updating installations.
