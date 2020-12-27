#!/usr/bin/env bash
set -euo pipefail

cat <<EOF > .env
IFTTT_KEY="$(lpass show --password "IFTTT webhook key")"
HONEYCOMB_KEY="$(lpass show --password "honeycomb.io API key")"
TELEGRAM_KEY="$(lpass show --password "fergal_test_bot Telegram bot")"
TELEGRAM_CHAT_ID="$(lpass show --password "Fergal cleaning Telegram chat Id")"
AUTH0_DOMAIN="$(lpass show --password "Fructify Auth0 domain")"
AUTH0_CLIENT_ID="$(lpass show --password "Fructify Auth0 client Id")"
AUTH0_CLIENT_SECRET="$(lpass show --password "Fructify Auth0 client secret")"
FLASK_SECRET_KEY="$(lpass show --password "Fructify Flask secret key")"
GOOGLE_CLIENT_ID="$(lpass show --password "Fructify Google client Id")"
GOOGLE_CLIENT_SECRET="$(lpass show --password "Fructify Google client secret")"
POSTGRES_DSN="$(lpass show --password "Fructify Postgres DSN")"
TELEGRAM_BOT_WEBHOOK_TOKEN="$(lpass show --password "Fructify Telegram bot webhook token")"
TELEGRAM_BOT_NAME="$(lpass show --password "Fructify Telegram bot name")"
EASYCRON_KEY="$(lpass show --password "Fructify EasyCron API token")"
EOF
