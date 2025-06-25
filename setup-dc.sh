#!/bin/bash

cd /var/www
docker compose build
docker compose up -d db --wait && docker compose up -d mautic_web --wait

echo "## Wait for basic-mautic_web-1 container to be fully running"
while ! docker exec basic-mautic_web-1 sh -c 'echo "Container is running"'; do
    echo "### Waiting for basic-mautic_web-1 to be fully running..."
    sleep 2
done

echo "## Check if Mautic is installed"
if docker compose exec -T mautic_web test -f /var/www/html/config/local.php && docker compose exec -T mautic_web grep -q "site_url" /var/www/html/config/local.php; then
    echo "## Mautic is installed already."
else
    # Check if the container exists and is running
    if docker ps --filter "name=basic-mautic_worker-1" --filter "status=running" -q | grep -q .; then
        echo "Stopping basic-mautic_worker-1 to avoid https://github.com/mautic/docker-mautic/issues/270"
        docker stop basic-mautic_worker-1
        echo "## Ensure the worker is stopped before installing Mautic"
        while docker ps -q --filter name=basic-mautic_worker-1 | grep -q .; do
            echo "### Waiting for basic-mautic_worker-1 to stop..."
            sleep 2
        done
    else
        echo "Container basic-mautic_worker-1 does not exist or is not running."
    fi
    echo "## Installing Mautic..."
    docker compose exec -T -u www-data -w /var/www/html mautic_web php ./bin/console mautic:install --force --admin_email {{EMAIL_ADDRESS}} --admin_password {{MAUTIC_PASSWORD}} http://{{IP_ADDRESS}}:{{PORT}}
fi

echo "## Starting all the containers"
docker compose up -d

DOMAIN="{{DOMAIN_NAME}}"

if [[ "$DOMAIN" == *"DOMAIN_NAME"* ]]; then
    echo "The DOMAIN variable is not set yet."
    exit 0
fi

DROPLET_IP=$(curl -s http://icanhazip.com)

# Extract base domain for DNS checks (e.g., if DOMAIN is m.superare.com.br, get superare.com.br)
if [[ "$DOMAIN" == m.* ]]; then
    BASE_DOMAIN=$(echo "$DOMAIN" | sed 's/^m\.//')
    echo "## Domain $DOMAIN detected as subdomain of $BASE_DOMAIN"
else
    BASE_DOMAIN="$DOMAIN"
    echo "## Using $DOMAIN as main domain"
fi

echo "## Checking if $DOMAIN points to this DO droplet..."

# First check if the domain is using Cloudflare
if dig +short NS $BASE_DOMAIN | grep -q "cloudflare"; then
    echo "## Domain is using Cloudflare DNS"
    
    # Check if the domain is proxied through Cloudflare
    if dig +short $DOMAIN | grep -q "cloudflare"; then
        echo "## Domain is proxied through Cloudflare, skipping DNS propagation check"
    else
        # Domain is using Cloudflare but not proxied, check the A record
        DOMAIN_IP=$(dig +short $DOMAIN)
        if [ "$DOMAIN_IP" != "$DROPLET_IP" ]; then
            echo "## $DOMAIN does not point to this droplet IP ($DROPLET_IP). Please update your Cloudflare A record."
            exit 1
        fi
    fi
else
    # Not using Cloudflare, do standard DNS check
    echo "## Domain is not using Cloudflare, performing standard DNS check"
    DOMAIN_IP=$(dig +short $DOMAIN)
    if [ "$DOMAIN_IP" != "$DROPLET_IP" ]; then
        echo "## $DOMAIN does not point to this droplet IP ($DROPLET_IP). Exiting..."
        exit 1
    fi
fi

echo "## $DOMAIN is available and points to this droplet. Nginx configuration..."

SOURCE_PATH="/var/www/nginx-virtual-host-$DOMAIN"
TARGET_PATH="/etc/nginx/sites-enabled/nginx-virtual-host-$DOMAIN"

# Remove the existing symlink if it exists
if [ -L "$TARGET_PATH" ]; then
    rm $TARGET_PATH
    echo "Existing symlink for $DOMAIN configuration removed."
fi

# Create a new symlink
ln -s $SOURCE_PATH $TARGET_PATH
echo "Symlink created for $DOMAIN configuration."

if ! nginx -t; then
    echo "Nginx configuration test failed, stopping the script."
    exit 1
fi

# Check if Nginx is running and reload to apply changes
if ! pgrep -x nginx > /dev/null; then
    echo "Nginx is not running, starting Nginx..."
    systemctl start nginx
else
    echo "Reloading Nginx to apply new configuration."
    nginx -s reload
fi

echo "## Check if Mautic is installed"
if docker compose exec -T mautic_web test -f /var/www/html/config/local.php && docker compose exec -T mautic_web test -f /var/www/html/config/local.php; then
    # Replace the site_url value with the domain
    echo "## Updating site_url in Mautic configuration..."
    docker compose exec -T mautic_web sed -i "s|'site_url' => '.*',|'site_url' => 'https://$DOMAIN',|g" /var/www/html/config/local.php
    
    # Enable Mautic API
    echo "## Enabling Mautic API..."
    if docker compose exec -T mautic_web grep -q "'api'" /var/www/html/config/local.php; then
        # Update existing API block
        echo "## Updating existing API configuration..."
        docker compose exec -T mautic_web sed -i "s/'api_enabled' => false/'api_enabled' => true/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'basic_auth_enabled' => false/'basic_auth_enabled' => true/g" /var/www/html/config/local.php
    else
        # Insert new API block before the closing );
        echo "## Adding new API configuration..."
        docker compose exec -T mautic_web sed -i "s/);$/'api' => [\n    'api_enabled' => true,\n    'basic_auth_enabled' => true,\n],\n);/" /var/www/html/config/local.php
    fi
    
    # Configure Mautic Email Settings
    echo "## Configuring Mautic Email Settings..."
    if docker compose exec -T mautic_web grep -q "'mailer'" /var/www/html/config/local.php; then
        # Update existing mailer block
        echo "## Updating existing mailer configuration..."
        docker compose exec -T mautic_web sed -i "s/'transport' => '.*'/'transport' => '${MAUTIC_MAILER_TRANSPORT}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'host' => '.*'/'host' => '${MAUTIC_MAILER_HOST}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'port' => '.*'/'port' => '${MAUTIC_MAILER_PORT}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'encryption' => '.*'/'encryption' => '${MAUTIC_MAILER_ENCRYPTION}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'user' => '.*'/'user' => '${MAUTIC_MAILER_USER}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'password' => '.*'/'password' => '${MAUTIC_MAILER_PASSWORD}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'auth_mode' => '.*'/'auth_mode' => '${MAUTIC_MAILER_AUTH_MODE}'/g" /var/www/html/config/local.php
    else
        # Insert new mailer block before the closing );
        echo "## Adding new mailer configuration..."
        docker compose exec -T mautic_web sed -i "s/);$/'mailer' => [\n    'transport' => '${MAUTIC_MAILER_TRANSPORT}',\n    'host' => '${MAUTIC_MAILER_HOST}',\n    'port' => '${MAUTIC_MAILER_PORT}',\n    'encryption' => '${MAUTIC_MAILER_ENCRYPTION}',\n    'user' => '${MAUTIC_MAILER_USER}',\n    'password' => '${MAUTIC_MAILER_PASSWORD}',\n    'auth_mode' => '${MAUTIC_MAILER_AUTH_MODE}',\n],\n);/" /var/www/html/config/local.php
    fi
    
    # Clear Mautic cache
    echo "## Clearing Mautic cache..."
    docker compose exec -T mautic_web rm -rf /var/www/html/var/cache/*
    echo "## Mautic API enabled successfully"
    
    # Restart containers to apply configuration changes
    echo "## Restarting containers to apply configuration changes..."
    docker compose restart mautic_web
    echo "## Containers restarted successfully"
fi

echo "## Script execution completed"
