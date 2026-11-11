---
name: chubby-domain-manager
description: Manage Chubby Media custom domains under chubby.media for ChatGPT Sites or Vercel-hosted websites. Use when the user asks to add, attach, bind, rename, migrate, remove, or verify a Chubby subdomain; connect a website to chubby.media; configure the matching Cloudflare DNS records; or diagnose DNS and HTTPS status.
---

# Chubby Domain Manager

Bind or rename `*.chubby.media` addresses end to end while preserving the website's hosting, data, authentication, and access policy.

## Portability and authorization

This skill uses the standard SKILL.md format and can be installed in Claude or Codex. Tool names in examples describe capabilities; discover the equivalent authorized tools in the current environment. Installing this skill grants no credentials or account permissions. If a provider connector is unavailable, use its official CLI or an authorized browser session where supported; otherwise explain the exact manual step. Do not bypass access controls. For a domain outside Chubby Media, use only the domain explicitly authorized by the user.

## Core workflow

1. Identify the exact website and hosting provider from the live source of truth. Do not infer the project solely from a title or an old URL.
2. Confirm the intended hostname. When the user did not specify one, propose the shortest clear English subdomain derived from the product name and state the assumption before creating it.
3. Check that the hostname has no existing `A`, `AAAA`, or `CNAME` record. Stop if it is already in use unless the user explicitly requests a replacement or rename.
4. Add the custom hostname to the hosting platform first. Copy the exact DNS records returned by that platform; never substitute remembered generic targets.
5. Add only those records in the `chubby.media` Cloudflare zone. Keep ordinary external-hosting CNAME records **DNS only** unless the hosting platform explicitly requires Cloudflare proxying.
6. Verify authoritative DNS, hosting-provider status, SSL status, HTTPS response, and a page-specific content marker.
7. Preserve the existing public/private access mode and application-level login. A custom domain change must not broaden access.
8. Report the final clickable URL and the access behavior in plain Chinese.

## Select the provider path

- For a ChatGPT Site, read [references/sites.md](references/sites.md) completely and use the Sites connector as the authoritative control plane.
- For a Vercel project, read [references/vercel.md](references/vercel.md) completely and use the project under the correct Chubby Vercel team.
- For all `chubby.media` DNS changes, read [references/cloudflare.md](references/cloudflare.md) completely before editing Cloudflare.

## Rename safely

Treat “改名” as a cutover, not an in-place text edit:

1. Check that the new hostname is unused.
2. Add the new hostname to the same hosting project.
3. Create its new DNS and validation records.
4. Wait until the new hostname, SSL certificate, HTTPS response, and expected page are all valid.
5. Remove the old hostname from the hosting project.
6. Delete only the old hostname's CNAME/A record and its provider-issued validation TXT records.
7. Verify the new records remain present and the old records are absent.

Do not remove the old address before the new address works.

## Safety rules

- Never edit or delete `MX`, `NS`, SPF, DKIM, DMARC, root-domain, or unrelated records for this workflow.
- Never change the apex `chubby.media` website unless the user explicitly names it.
- Never overwrite an existing record with the same hostname without resolving the conflict first.
- Never expose environment variables, access codes, API keys, verification tokens, or opaque project IDs in the final response.
- Keep provider-generated `.chatgpt.site` or `.vercel.app` addresses unless the user explicitly requests their removal; they are useful fallbacks.
- If the app is private or uses company email/access codes, verify that behavior still appears on the custom hostname.
- When browser interaction is required, load and follow the available Chrome/browser control skill. Use exact visible labels and verify each saved record.

## Completion standard

Finish only when all applicable checks pass:

- Hosting platform lists the new custom hostname as active or valid.
- SSL/HTTPS is active.
- Authoritative DNS returns the expected target and required TXT records.
- A real HTTPS GET reaches the expected website or its intended sign-in/access page.
- A rename leaves only the intended hostname attached to the hosting project.
- Old DNS records are absent after a rename.

If certificate issuance is still pending, keep polling within the turn and do not claim completion.

## Final response

Lead with the new clickable URL. Briefly state:

- DNS and HTTPS status.
- Which existing website it points to.
- Whether access remains public, ChatGPT-authenticated, or protected by company email/access code.
- Whether an old hostname was retained or removed.

Do not include internal tokens, DNS validation values, project IDs, or command output.
