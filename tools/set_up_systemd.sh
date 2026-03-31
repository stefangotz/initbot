#!/bin/sh

# SPDX-FileCopyrightText: 2026 Stefan Götz <github.nooneelse@spamgourmet.com>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

set -ue

REPO_DIR="$(cd "$(dirname "$(realpath "${0}")")"/.. && pwd)"
SERVICE_USER="$(id -un)"
export REPO_DIR SERVICE_USER
TEMPLATE="$REPO_DIR/tools/initbot.service.template"
ENVSUBST_VARS="\${SERVICE_DESCRIPTION} \${SERVICE_USER} \${REPO_DIR} \${RUN_SCRIPT} \${APP_ENV_SUFFIX}"
DRY_RUN=0

for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY_RUN=1 ;;
        *)
            printf 'Usage: %s [--dry-run]\n' "$0" >&2
            exit 1
            ;;
    esac
done

printf 'Note: the systemd service will run directly from the cloned repository:\n'
printf '\n'
printf '  %s\n' "$REPO_DIR"
printf '\n'
printf 'Running server-side applications from a source tree is convenient\n'
printf 'but is not the recommended approach for production deployments. For a\n'
printf 'more robust setup, consider installing the application to a fixed path\n'
printf '(e.g. /opt/initbot) and running it under a dedicated system user account.\n'
printf 'See the TODO comments in the generated unit files.\n'
printf '\n'

write_unit() {
    # $1=unit_path  $2=description  $3=run_script  $4=app_env_suffix
    if [ "$DRY_RUN" = "1" ]; then
        printf '=== %s ===\n' "$1"
        SERVICE_DESCRIPTION="$2" RUN_SCRIPT="$3" APP_ENV_SUFFIX="$4" \
            envsubst "$ENVSUBST_VARS" < "$TEMPLATE"
        printf '\n'
    else
        SERVICE_DESCRIPTION="$2" RUN_SCRIPT="$3" APP_ENV_SUFFIX="$4" \
            envsubst "$ENVSUBST_VARS" < "$TEMPLATE" | sudo tee "$1" > /dev/null
        printf 'Wrote %s\n' "$1"
    fi
}

prompt_systemctl() {
    # $1=action  $2=service
    if [ "$DRY_RUN" = "1" ]; then
        printf 'Would run: sudo systemctl %s %s (if confirmed)\n' "$1" "$2"
    else
        printf 'Run sudo systemctl %s %s? [y/N] ' "$1" "$2"
        read -r answer
        case "$answer" in
            y|Y) sudo systemctl "$1" "$2" ;;
        esac
    fi
}

write_unit \
    /etc/systemd/system/initbot.service \
    "" \
    "" \
    ""

if [ "$DRY_RUN" = "1" ]; then
    printf 'Would run: sudo systemctl daemon-reload\n'
else
    sudo systemctl daemon-reload
fi

prompt_systemctl enable initbot
prompt_systemctl start initbot
