# Future improvements

Backlog of things worth doing, roughly in priority order.

## Backups

All state lives on one disk (`media-stack/`, `pihole/etc-*`, `caddy/caddy_data`), so a disk failure loses every service's config and database.

- Add a second drive, then back up with restic or Kopia on a schedule.
- Back up configs and databases (Jellyfin, Radarr, Sonarr, Prowlarr, qBittorrent, Portainer, Pi-hole, Caddy data). The media library itself is optional.
- Keep `.env` in a password manager, since it is git-ignored.
- Include `caddy/caddy_data`, so the Caddy root CA survives a rebuild and devices don't need to trust a new one.
- Consider an offsite copy (for example Backblaze B2) once a local copy exists.

## DNS redundancy

The router's secondary DNS is Google, so lookups continue if Pi-hole is down, but ad blocking and `*.home.arpa` resolution stop. A second Pi-hole kept in sync (Nebula Sync) would avoid that.

## Certificates

Caddy uses its internal CA (`local_certs`), so each device must trust the root once. Options if that becomes a burden:

- A real domain with a Caddy DNS-01 wildcard cert (no device setup; replaces `.home.arpa`).
- Tailscale HTTPS (`tailscale serve`), which gives trusted `*.ts.net` names but one hostname per node.

## Identity and access

- SSO with Authelia (or Authentik) in front of the *arr UIs, with OIDC for apps that support it. Depends on the certificate decision above.
- Put Portainer behind `tecnativa/docker-socket-proxy`.

## Self-hosted replacements

- Vaultwarden (passwords), which requires trusted HTTPS.
- Immich (photos).
- Nextcloud or Syncthing (files and sync).

## Monitoring

- Uptime Kuma with ntfy for alerts when DNS, gluetun, or a service is down.
