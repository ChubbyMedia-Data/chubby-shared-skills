# Vercel custom-domain workflow

Use this path when the website is deployed as a Vercel project.

## Inspect

1. Confirm the project belongs to the intended Chubby Vercel team, not a personal account.
2. Confirm the current production deployment and fallback `.vercel.app` URL.
3. Inspect **Project Settings -> Domains** before adding anything.

## Add

1. Add the full custom hostname to the project's Production environment.
2. Copy the exact DNS requirement Vercel displays. Project-specific CNAME targets may differ from generic Vercel examples.
3. Add the corresponding DNS record in Cloudflare. For a normal subdomain, use the exact CNAME target and set it to **DNS only** unless Vercel explicitly instructs otherwise.
4. Return to Vercel and refresh the domain status.
5. Wait for **Valid Configuration** and completed SSL certificate generation.
6. Verify an HTTPS GET and a page-specific content marker.

## Rename or remove

1. Add and validate the new hostname first.
2. Remove the old custom hostname from the Vercel project only after the new URL works.
3. Delete only the old hostname's provider-specific Cloudflare records.
4. Retain the `.vercel.app` fallback URL.

Do not move a private, server-backed ChatGPT Site to Vercel merely to add a domain. A migration requires editable source, server handlers, environment variables, authentication replacement, and full functional validation.
