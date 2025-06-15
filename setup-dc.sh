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

# Check if SKIP_DNS_CHECK is set to true
if [ "${SKIP_DNS_CHECK:-false}" = "true" ]; then
    echo "## DNS check skipped as requested"
    DROPLET_IP=$(curl -s http://icanhazip.com)
else
    DROPLET_IP=$(curl -s http://icanhazip.com)
    echo "## Checking if $DOMAIN points to this DO droplet..."

    # First check if the domain is using Cloudflare
    if dig +short NS $DOMAIN | grep -q "cloudflare"; then
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
    docker compose exec -T mautic_web sed -i "s|'site_url' => '.*',|'site_url' => 'https://m.$DOMAIN',|g" /var/www/html/config/local.php
fi

echo "## Script execution completed"
