#!/bin/sh
set -eu

# Read DB password from secret if not already provided.
if [ -z "${DB_PASSWORD:-}" ] && [ -n "${DB_PASSWORD_FILE:-}" ] && [ -f "${DB_PASSWORD_FILE}" ]; then
  export DB_PASSWORD="$(cat "${DB_PASSWORD_FILE}")"
fi

exec "$@"
