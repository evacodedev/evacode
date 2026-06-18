#!/bin/bash
# First-time Let's Encrypt certificate setup.
# Run once on the server before starting the full stack.
# Usage: bash init-letsencrypt.sh

set -e

DOMAIN="www.evacode.org"
EMAIL="sales@evacode.org"
STAGING=0  # Set to 1 for dry-run testing without hitting rate limits

CONF_PATH="./data/certbot/conf"
WWW_PATH="./data/certbot/www"

mkdir -p "$CONF_PATH/live/$DOMAIN"
mkdir -p "$WWW_PATH"

# --- Step 1: create a temporary self-signed cert so nginx can start ---
if [ ! -f "$CONF_PATH/live/$DOMAIN/fullchain.pem" ]; then
  echo "### Creating temporary self-signed certificate..."
  openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$CONF_PATH/live/$DOMAIN/privkey.pem" \
    -out    "$CONF_PATH/live/$DOMAIN/fullchain.pem" \
    -subj "/CN=localhost" 2>/dev/null
fi

# --- Step 2: build and start nginx so it can serve the ACME challenge ---
echo "### Building and starting nginx..."
docker compose up --force-recreate --build -d nginx
sleep 5

# --- Step 3: request the real certificate ---
echo "### Requesting Let's Encrypt certificate for $DOMAIN..."
STAGING_FLAG=""
if [ "$STAGING" = "1" ]; then
  STAGING_FLAG="--staging"
  echo "(staging mode — no real certificate will be issued)"
fi

docker compose run --rm --entrypoint certbot certbot certonly \
  --webroot \
  --webroot-path=/var/www/certbot \
  --force-renewal \
  $STAGING_FLAG \
  --email "$EMAIL" \
  --agree-tos \
  --no-eff-email \
  -d "$DOMAIN" \
  -d "evacode.org"

# --- Step 4: reload nginx with the real certificate ---
echo "### Reloading nginx..."
docker compose exec nginx nginx -s reload

echo ""
echo "Done! Certificate is active. Start the full stack with:"
echo "  docker compose up -d"
