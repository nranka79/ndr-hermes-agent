# jobs.ahfl.in — deployment checklist (live)

Deployed on the box. `jobs.ahfl.in.nginx` is a snapshot of the live
vhost (certbot manages the TLS block); `jobs.ahfl.in.nginx.draft` is the
HTTP-only bootstrap config used before the certificate existed.
`docker-compose.jobs-board.snippet.yml` matches the live `jobs-board` /
`jobs-oauth2-proxy` services. The canonical compose file remains
`hermes-apps-stack/docker-compose.prod.yml`.

The steps below are kept as the reproducible deploy/rollback recipe.

## Prerequisites — yours, not mine

1. **DNS**: add an A record `jobs.ahfl.in -> 91.99.219.247`. Nothing below
   works until this resolves (certbot's HTTP-01 challenge needs it).
2. **Google OAuth redirect URI**: in Google Cloud Console, on the OAuth
   client already used by chat.ahfl.in (`GOOGLE_CLIENT_ID` in
   `/opt/hermes/.env`), add `https://jobs.ahfl.in/oauth2/callback` to the
   authorized redirect URIs list. One client, multiple redirect URIs —
   no new OAuth app needed.
3. **Access list**: who should be able to log into jobs.ahfl.in? The
   existing chat.ahfl.in allowlist (`/etc/oauth2-proxy/emails.txt` on the
   box) has 15 addresses — broad, org-wide. Job cards can carry
   genuinely sensitive content (legal matters, drafted messages to named
   people). Decide the list before step 4 below; default assumption
   until told otherwise: just `ndr@ahfl.in`.

## Open item from the previous increment (separate, not blocking this)

The Telegram busy-session bypass fix (`ops/patches/0002-plugin-command-busy-bypass.patch`)
is still unapplied — its target file (`hermes_cli/commands.py`) isn't
bind-mounted into the container, so fixing it durably needs a
docker-compose edit + container recreate, which is still awaiting your
go-ahead from the prior conversation. Independent of everything here;
not needed for the board to work.

## Deploy steps, in order

```bash
# 0. Confirm DNS has propagated
dig +short jobs.ahfl.in        # must show 91.99.219.247

# 1. Allowlist file
mkdir -p /opt/hermes/oauth2-proxy-jobs
cat > /opt/hermes/oauth2-proxy-jobs/emails.txt <<'EOF'
ndr@ahfl.in
EOF
# add more lines here if more people should have access

# 2. New secret for this app's own session cookie (do NOT reuse chat's)
openssl rand -base64 32 | cut -c1-32
# append the result to /opt/hermes/.env as:
#   JOBS_OAUTH2_PROXY_COOKIE_SECRET=<generated value>

# 3. Back up compose before editing (same discipline as every prior change)
cp /opt/hermes/docker-compose.prod.yml /opt/hermes/docker-compose.prod.yml.pre-jobs-board.bak

# 4. Paste the two service blocks from docker-compose.jobs-board.snippet.yml
#    into docker-compose.prod.yml under `services:`.

# 5. VALIDATE before touching anything running
docker compose -f /opt/hermes/docker-compose.prod.yml config >/dev/null
#    ^ must exit 0 and print no errors. If it errors, STOP and fix the
#    YAML before proceeding -- this is exactly the step skipped when
#    config.yaml got corrupted earlier in this project; not skipping it
#    again.

# 6. Bring up ONLY the two new services (no --no-deps risk to anything
#    else; these are brand new service names, nothing else references them)
docker compose -f /opt/hermes/docker-compose.prod.yml up -d jobs-board jobs-oauth2-proxy

# 7. Sanity check from the host, before any public exposure
curl -s http://127.0.0.1:8900/health                    # {"ok": true}
curl -s -o /dev/null -w "%{http_code}\n" http://127.0.0.1:4182/   # likely a redirect to Google

# 8. nginx vhost (HTTP only first, for the certbot challenge)
cp jobs.ahfl.in.nginx.draft /etc/nginx/sites-available/jobs.ahfl.in
ln -s /etc/nginx/sites-available/jobs.ahfl.in /etc/nginx/sites-enabled/jobs.ahfl.in
nginx -t && systemctl reload nginx

# 9. Issue the cert -- certbot rewrites the vhost file in place to add
#    the 443 block + https redirect, same shape as every other
#    *.ahfl.in vhost on this box.
certbot --nginx -d jobs.ahfl.in

# 10. Open https://jobs.ahfl.in in a browser -> should hit Google's
#     login screen, then land on the job list after auth.
```

## Rollback

```bash
docker compose -f /opt/hermes/docker-compose.prod.yml stop jobs-board jobs-oauth2-proxy
docker compose -f /opt/hermes/docker-compose.prod.yml rm -f jobs-board jobs-oauth2-proxy
rm /etc/nginx/sites-enabled/jobs.ahfl.in
systemctl reload nginx
cp /opt/hermes/docker-compose.prod.yml.pre-jobs-board.bak /opt/hermes/docker-compose.prod.yml
```
Nothing here can affect `hermes-hermes-1` or `hermes-apps-1` — both new
services are additive, and stopping/removing them touches nothing else.

## Known gaps, stated plainly

- **No "admin sees all" distinction in the UI** — every authenticated
  person sees every job. Fine for a 1-2 person allowlist; would need
  real work for a bigger team.
- **Mic dictation requires HTTPS** (browsers refuse `getUserMedia` on
  plain HTTP for any host other than `localhost`) — this is exactly why
  step 9 (the real cert) has to happen before dictation can be tested at
  all, even though the board itself would work over bare HTTP earlier.
