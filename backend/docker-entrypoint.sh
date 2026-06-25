#!/usr/bin/env sh
set -e

if [ "${RUN_MIGRATIONS_ON_STARTUP:-true}" = "true" ]; then
  python -m alembic upgrade head
fi

exec "$@"
