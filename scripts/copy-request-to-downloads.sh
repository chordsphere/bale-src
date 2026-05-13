#!/usr/bin/env bash
set -euo pipefail
src="$BALE_REPO_ROOT/.bale/outbox/request-$BALE_SESSION_ID.tar.gz"
dst="/mnt/c/Users/chord/Downloads/"
cp "$src" "$dst"
printf '[post_pack] copied %s -> %s/\n' "$src" "$dst"
