#!/usr/bin/env bash
# Nightly offsite backup of homelab config to R2 with restic. Run from cron; see README.
set -euo pipefail

cd "$(dirname "$0")/.."
set -a
. ./.env
set +a

: "${RESTIC_REPOSITORY:?set in .env}"
: "${RESTIC_PASSWORD:?set in .env}"
: "${R2_ACCESS_KEY_ID:?set in .env}"
: "${R2_SECRET_ACCESS_KEY:?set in .env}"

ROOT="$PWD"
VW_BACKUPS="${VAULTWARDEN_BACKUP_DIR:-$ROOT/vaultwarden/backups}"
# Apps with live SQLite databases; stopped briefly for a consistent copy. Pi-hole stays up (DNS).
STOP=(sonarr radarr prowlarr bazarr seerr jellyfin qbittorrent)

restic() {
  docker run --rm \
    -e RESTIC_REPOSITORY -e RESTIC_PASSWORD \
    -e AWS_ACCESS_KEY_ID="$R2_ACCESS_KEY_ID" \
    -e AWS_SECRET_ACCESS_KEY="$R2_SECRET_ACCESS_KEY" \
    -e AWS_DEFAULT_REGION=auto \
    -v "$ROOT:/src:ro" \
    -v "$VW_BACKUPS:/vw-backups:ro" \
    restic/restic:0.18.0 "$@"
}

restic snapshots >/dev/null 2>&1 || restic init

docker compose stop "${STOP[@]}"
trap 'docker compose start "${STOP[@]}"' EXIT

restic backup \
  --host homelab \
  --exclude '/src/media-stack/jellyfin/cache' \
  --exclude '/src/media-stack/jellyfin/transcodes' \
  --exclude '/src/media-stack/jellyfin/metadata' \
  --exclude '/src/media-stack/ombi' \
  --exclude '/src/media-stack/gluetun' \
  --exclude '/src/media-stack/*/MediaCover' \
  --exclude '/src/vaultwarden/data/db.sqlite3*' \
  --exclude '/src/vaultwarden/data/tmp' \
  /src/.env \
  /src/media-stack \
  /src/pihole/etc-pihole/pihole.toml \
  /src/pihole/etc-pihole/gravity.db \
  /src/vaultwarden/data \
  /vw-backups

restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune
