#!/bin/sh
set -eu

# Read password from secret file
if [ -f "/run/secrets/postgres_password" ]; then
  DB_PASSWORD=$(cat /run/secrets/postgres_password)
  export DB_PASSWORD
  
  # Replace password_file with actual password in DATABASES string
  if [ -n "${DATABASES:-}" ]; then
    export DATABASES=$(echo "$DATABASES" | sed "s|password_file=/run/secrets/postgres_password|password=$DB_PASSWORD|g")
  fi
fi

# Execute the original entrypoint
exec /opt/pgbouncer/entrypoint.sh "$@"

