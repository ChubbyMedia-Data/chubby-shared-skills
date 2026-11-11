# ChatGPT Sites custom-domain workflow

Use this path when the current production URL ends in `.chatgpt.site` or the project is confirmed by the Sites connector.

## Inspect

1. If a Sites hosting skill is installed, read it before using Sites tools; otherwise discover the available Sites connector and its documentation.
2. Use `sites_list_sites` only when no trusted project ID is already available.
3. Match the live project by title, slug, current live URL, ownership role, and description. Treat the returned project ID as opaque.
4. Use `sites_get_site` when access mode or the current live URL needs confirmation.
5. Use `sites_list_custom_domains` to inspect current bindings before adding or removing anything.

## Add

1. Call `sites_add_custom_domain` with the exact project ID and bare hostname.
2. Record the returned CNAME or apex targets and every validation record.
3. Configure those values in Cloudflare exactly as returned.
4. Call `sites_refresh_custom_domain_status` until all of these are true:
   - `status` is `active`.
   - `provider_status` is `active`.
   - `ssl_status` is `active`.
5. Verify the website with an HTTPS GET and a page-specific content marker.

Temporary states such as `pending_validation` and `active_redeploying` are normal. Continue polling; a temporary 404 during redeployment is not completion.

## Access

Custom-domain work must not change `access_mode` or `access_policy`.

- For a private Site, expect a ChatGPT sign-in page or 401 when unauthenticated.
- For a public Site with application-level protection, expect its own company-email/access-code page.
- Verify the existing access behavior on the new hostname before completion.

## Rename or remove

1. Activate and verify the new hostname first.
2. Call `sites_remove_custom_domain` for the old custom-domain ID.
3. Call `sites_list_custom_domains` again and confirm only the intended hostname remains.
4. Remove the old provider-specific DNS records from Cloudflare.

Do not remove the underlying `.chatgpt.site` production URL.
