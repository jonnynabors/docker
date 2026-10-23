# Future improvements

Backlog of things worth doing, roughly in priority order.

## Backups

Configs and Vaultwarden data are backed up nightly to Cloudflare R2 by `scripts/backup.sh` (see the README). Remaining gaps:

- The media library and downloads are not backed up (by choice; they are re-downloadable).
- Nothing alerts if a nightly backup fails or stops running (see Monitoring).
- Do a periodic test restore into a scratch directory.
- Keep `RESTIC_PASSWORD` in a copy that does not live only on this machine.
- Add a second drive for local redundancy once the ST6000NM0115 arrives.

## DNS redundancy

The router's secondary DNS is Google, so lookups continue if Pi-hole is down, but ad blocking and `*.rackcellar.com` resolution stop. A second Pi-hole kept in sync (Nebula Sync) would avoid that.

## Certificates

Caddy serves `*.rackcellar.com` with a wildcard Let's Encrypt cert (DNS-01 via Cloudflare), so no device setup is needed. Names have no public DNS records and resolve only through Pi-hole (and Tailscale split DNS plus a subnet route for remote access).

## Identity and access

- SSO with Authelia (or Authentik) in front of the *arr UIs, with OIDC for apps that support it.
- Put Portainer behind `tecnativa/docker-socket-proxy`.

## Self-hosted replacements

- Immich (photos).
- Nextcloud or Syncthing (files and sync).

## Monitoring

- Uptime Kuma with ntfy for alerts when DNS, gluetun, or a service is down.
- Backup monitoring: a Uptime Kuma push monitor that `scripts/backup.sh` pings on success, so a missed or failed nightly run alerts (heartbeat interval a bit over 24h).
- Disk health: `smartd` (smartmontools) alerts for the refurbished ST3000DM001, which has a poor failure record, with ntfy or email notifications. Add the ST6000NM0115 when it is installed.
