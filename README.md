# Homelab

Single Docker Compose project (`homelab`) running DNS, a reverse proxy, and a VPN-routed media stack.

## Architecture

```mermaid
flowchart LR
    LAN([LAN clients])
    Mullvad[(Mullvad WireGuard)]

    subgraph host[Docker host]
        pihole[Pi-hole<br/>DNS :53, UI :8080]
        caddy[Caddy<br/>:80 / :443]
        ombi[Ombi :3579]
        seerr[Seerr :5055]
        portainer[Portainer :9000]

        subgraph vpn[gluetun network namespace]
            gluetun{{gluetun}}
            jellyfin[Jellyfin :8096]
            qbit[qBittorrent :8112]
            radarr[Radarr :7878]
            sonarr[Sonarr :8989]
            prowlarr[Prowlarr :9696]
        end
    end

    LAN -- DNS --> pihole
    LAN -- "*.home.arpa" --> caddy
    caddy --> pihole
    caddy --> ombi
    caddy --> seerr
    caddy --> portainer
    caddy -- via gluetun ports --> jellyfin & qbit & radarr & sonarr & prowlarr
    gluetun == tunnel ==> Mullvad
```

## Services

| Service     | URL                          | Behind VPN |
| ----------- | ---------------------------- | ---------- |
| Pi-hole     | `pihole.home.arpa` (`:8080`) | no         |
| Jellyfin    | `jellyfin.home.arpa`         | yes        |
| qBittorrent | `torrent.home.arpa`          | yes        |
| Radarr      | `radarr.home.arpa`           | yes        |
| Sonarr      | `sonarr.home.arpa`           | yes        |
| Prowlarr    | `prowlarr.home.arpa`         | yes        |
| Ombi        | `ombi.home.arpa`             | no         |
| Seerr       | `seerr.home.arpa`            | no         |
| Portainer   | `portainer.home.arpa`        | no         |

Services behind the VPN use `network_mode: service:gluetun`, so their ports are published on `gluetun`. They restart with it (`depends_on` with `restart: true`).

## Setup

Requires Docker Compose 2.17 or newer.

1. Create the env file and fill it in:

   ```sh
   cp .env.example .env
   ```

   | Variable                | Required | Description                                                                 |
   | ----------------------- | -------- | --------------------------------------------------------------------------- |
   | `WIREGUARD_PRIVATE_KEY` | yes      | Mullvad WireGuard private key                                               |
   | `WIREGUARD_ADDRESSES`   | yes      | Mullvad WireGuard address                                                   |
   | `PIHOLE_PASSWORD`       | yes      | Pi-hole web UI password                                                     |
   | `MEDIA_ROOT`            | no       | Media library root, default `/mnt/storage` (needs a `downloads/` subfolder) |

2. Start everything from the repo root:

   ```sh
   docker compose up -d
   ```

3. Point the router's DNS (or individual clients) at the host, and add a Pi-hole local DNS record for each `*.home.arpa` name pointing at the host IP.

## Layout

| Path                                            | Purpose                                           |
| ----------------------------------------------- | ------------------------------------------------- |
| `docker-compose.yml`                            | All services                                      |
| `caddy/Caddyfile`                               | Reverse proxy routes (`local_certs`, internal CA) |
| `media-stack/`, `pihole/etc-*`, `caddy/caddy_*` | Runtime state, git-ignored                        |
| `.env`                                          | Secrets, git-ignored                              |

## Verifying the VPN

Gluetun adds an iptables kill switch: its `OUTPUT` policy is `DROP`, and it only allows the Docker and LAN subnets (`FIREWALL_OUTBOUND_SUBNETS`), the Mullvad endpoint, and `tun0`. Containers using `network_mode: service:gluetun` share that namespace, so if the tunnel drops their traffic is blocked, not sent out over the normal connection.

To check it from the Docker host:

```sh
curl -s https://am.i.mullvad.net/ip                                  # host's real IP
docker exec qbittorrent wget -qO- https://am.i.mullvad.net/json      # should show mullvad_exit_ip: true
docker exec gluetun iptables -S OUTPUT                               # policy DROP, no rule for eth0 to the internet
docker logs gluetun 2>&1 | grep -E 'Public IP|leak check'
```

The two IPs must differ. DNS inside the namespace goes through gluetun's own resolver, and its upstream queries leave through the tunnel.

## Notes

- Caddy uses its internal CA; trust its root certificate (`caddy/caddy_data/caddy/pki/authorities/local/root.crt`) on clients to avoid browser warnings.
- Jellyfin reserves an Nvidia GPU; remove its `deploy` block on a host without one.
- Image versions are pinned in `docker-compose.yml` and bumped by Renovate pull requests (`renovate.json`). Gluetun is pinned by digest because the deployed build is newer than the latest release tag.
