# Cloudflare DNS workflow for chubby.media

Use this reference for every `chubby.media` DNS edit.

## Before editing

1. Query available tools for a Cloudflare API or connector first. If none can perform the required DNS mutation, load the Chrome/browser-control skill and use the authenticated Cloudflare dashboard.
2. Open the `chubby.media` zone and confirm the account can edit DNS records.
3. Check the requested hostname through public or authoritative DNS before creating it.

## Add records

In **DNS -> Records -> Add record**, reproduce the hosting provider's output exactly:

- For a subdomain CNAME, enter only the subdomain label in **Name** when practical; Cloudflare displays the complete hostname.
- Enter the exact target in **Target**.
- Set **Proxy status** to **DNS only** for Sites or Vercel custom-domain setup unless the provider explicitly requires proxying.
- Leave **TTL** on **Auto** unless the provider specifies another value.
- Add every provider-issued TXT validation record with its exact name and value.

After each save, confirm the row appears with the intended type, name, content, proxy status, and TTL.

## Verify

1. Query the authoritative Cloudflare nameservers when a recursive resolver is stale.
2. Confirm the expected CNAME/A record and every required TXT value.
3. Return to the hosting provider and refresh validation.
4. Verify HTTPS only after the provider reports an active certificate.

## Remove old records after a rename

1. Filter the DNS table by the complete old hostname.
2. Confirm the result contains only the old CNAME/A record and the old provider validation TXT records.
3. Delete each exact old record.
4. Re-query authoritative DNS to confirm absence.
5. Re-query the new hostname to confirm its records remain intact.

Never delete records merely because they contain the word `marketing`, `onboarding`, or another broad product term. Match the complete old hostname and validation-record names.

## Protected records

Do not edit or delete these unless the user explicitly requests that separate operation:

- `MX` mail-routing records.
- SPF, DKIM, or DMARC TXT records.
- `NS` records or nameservers.
- Apex `chubby.media` A/AAAA/CNAME records.
- Unrelated product subdomains.
