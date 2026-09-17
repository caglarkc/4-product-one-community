#!/usr/bin/env bash
set -Eeuo pipefail
umask 077
BASE=/opt/first/backend
RELEASE=${1:?release required}
[[ "$RELEASE" =~ ^[0-9]{8}T[0-9]{6}-[a-f0-9]{12}$ ]] || exit 2
SOURCE="$BASE/releases/$RELEASE"
export FIRST_ENV_FILE="$BASE/shared/.env"
export FIRST_RELEASE="$RELEASE"
mkdir -p "$BASE/backups"
exec 9>"$BASE/deploy.lock"
flock -n 9 || { echo 'Another FIRST deployment is active'; exit 1; }
previous=''
if [[ -L "$BASE/current" && -f "$BASE/current/compose.yaml" ]]; then
  previous=$(readlink -f "$BASE/current")
  [[ "$previous" == "$BASE/releases/"* ]] || { echo 'Unexpected current release'; exit 1; }
elif [[ -e "$BASE/current" ]]; then
  echo 'Current path exists but is not a managed release'; exit 1
fi
for container in $(docker ps -aq --filter label=com.docker.compose.project=first); do
  owner=$(docker inspect --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' "$container")
  [[ "$owner" == "$BASE/releases/"* ]] || { echo 'Compose project first belongs to another deployment'; exit 1; }
done
for volume in first_postgres-data first_redis-data; do
  if docker volume inspect "$volume" >/dev/null 2>&1; then
    owner=$(docker volume inspect --format '{{index .Labels "io.first.managed"}}' "$volume")
    [[ "$owner" == "$BASE" ]] || { echo 'Existing FIRST volume has unknown ownership'; exit 1; }
  fi
done
if docker network inspect first_default >/dev/null 2>&1; then
  owner=$(docker network inspect --format '{{index .Labels "io.first.managed"}}' first_default)
  [[ "$owner" == "$BASE" ]] || { echo 'Existing FIRST network has unknown ownership'; exit 1; }
fi
backend_replaced=false
on_exit() {
  code=$?
  trap - EXIT
  if [[ "$code" != 0 && -n "$previous" ]]; then
    if [[ -f "$BASE/backups/$RELEASE.env" ]]; then
      cp "$BASE/backups/$RELEASE.env" "$FIRST_ENV_FILE"
    fi
    if [[ "$backend_replaced" == true ]]; then
      export FIRST_RELEASE=${previous##*/}
      docker compose --env-file "$FIRST_ENV_FILE" -p first -f "$previous/compose.yaml" up -d --no-deps backend || true
    fi
    echo 'Failed deployment: previous configuration restored; database migrations were NOT reversed. Check schema compatibility.'
  fi
  exit "$code"
}
if [[ -n "$previous" ]]; then cp "$FIRST_ENV_FILE" "$BASE/backups/$RELEASE.env"; fi
trap on_exit EXIT
python3 "$SOURCE/deploy/configure.py" "$FIRST_ENV_FILE"
cd "$SOURCE"
dc() { docker compose --env-file "$FIRST_ENV_FILE" -p first -f "$SOURCE/compose.yaml" "$@"; }
dc config --quiet
# A newly provisioned FIRST instance must never take another service's port.
if [[ -z "$previous" ]] && ss -H -lnt 'sport = :18081' | grep -q . && ! docker ps --filter label=com.docker.compose.project=first --filter label=com.docker.compose.service=backend --format '{{.Ports}}' | grep -Fq '127.0.0.1:18081->8000/tcp'; then
  echo 'Port 18081 is already occupied; no service was changed.'; exit 1
fi
dc build backend
dc up -d --wait --wait-timeout 120 db redis
if [[ -n "$previous" ]]; then
  dc exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$BASE/backups/$RELEASE.dump"
fi
dc run --rm --no-deps backend python manage.py check
dc run --rm --no-deps backend python manage.py migrate --noinput
dc run --rm --no-deps backend python manage.py migrate --check
dc run --rm --no-deps backend python manage.py shell -c "from django.db import connection; from accounts.security import client; connection.ensure_connection(); assert client().ping(); print('PostgreSQL and Redis connections passed')"
backend_replaced=true
dc up -d --wait --wait-timeout 120 --no-deps backend
curl --fail --silent --max-time 10 http://127.0.0.1:18081/health/
ln -sfn "$SOURCE" "$BASE/current.next"
mv -Tf "$BASE/current.next" "$BASE/current"
dc ps
echo "FIRST release $RELEASE healthy. Persistent data and other projects preserved."
