#!/bin/sh
set -eu

if [ -z "${DB_PASSWORD:-}" ] && [ -n "${DB_PASSWORD_FILE:-}" ] && [ -f "${DB_PASSWORD_FILE}" ]; then
  export DB_PASSWORD="$(cat "${DB_PASSWORD_FILE}")"
fi

exec "$@"
