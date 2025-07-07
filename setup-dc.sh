#!/bin/bash

set -e

# Function to URL-encode a string
url_encode() {
    local string="${1}"
    local strlen=${#string}
    local encoded=""
    local pos c o

    for (( pos=0 ; pos<strlen ; pos++ )); do
        c=${string:$pos:1}
        case "$c" in
            [-_.~a-zA-Z0-9] ) o="${c}" ;;
            * )               printf -v o '%%%02x' "'$c"
        esac
        encoded+="${o}"
    done
    echo "${encoded}"
}

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to log success
log_success() {
    log "✅ $1"
}

# Function to log warning
log_warning() {
    log "⚠️  $1"
}

# Function to log error
log_error() {
    log "❌ $1"
}

# Function to log info
log_info() {
    log "ℹ️  $1"
}

cd /var/www
log_info "=== Starting Docker Compose Build ==="
docker compose build --no-cache --progress=plain 2>&1 | tee /var/log/docker_build.log
log_success "=== Docker Compose Build Finished ==="

log_info "Starting database and web containers..."
docker compose up -d db --wait && docker compose up -d mautic_web --wait
log_success "Database and web containers started successfully"

log_info "Waiting for basic-mautic_web-1 container to be fully running"
while ! docker exec basic-mautic_web-1 sh -c 'echo "Container is running"'; do
    log_info "Waiting for basic-mautic_web-1 to be fully running..."
    sleep 2
done
log_success "Container basic-mautic_web-1 is fully running"

log_info "Checking if Mautic is already installed..."
if docker compose exec -T mautic_web test -f /var/www/html/config/local.php && docker compose exec -T mautic_web grep -q "site_url" /var/www/html/config/local.php; then
    log_success "Mautic is already installed"
else
    # Check if the container exists and is running
    if docker ps --filter "name=basic-mautic_worker-1" --filter "status=running" -q | grep -q .; then
        log_info "Stopping basic-mautic_worker-1 to avoid https://github.com/mautic/docker-mautic/issues/270"
        docker stop basic-mautic_worker-1
        log_info "Ensuring the worker is stopped before installing Mautic"
        while docker ps -q --filter name=basic-mautic_worker-1 | grep -q .; do
            log_info "Waiting for basic-mautic_worker-1 to stop..."
            sleep 2
        done
        log_success "Worker container stopped successfully"
    else
        log_info "Container basic-mautic_worker-1 does not exist or is not running"
    fi
    log_info "Installing Mautic..."
    docker compose exec -T -u www-data -w /var/www/html mautic_web php ./bin/console mautic:install --force --admin_email {{EMAIL_ADDRESS}} --admin_password {{MAUTIC_PASSWORD}} http://{{IP_ADDRESS}}:{{PORT}}
    log_success "Mautic installation completed"
fi

log_info "Starting all containers"
log_info "=== Starting Docker Compose Up ==="
docker compose up -d 2>&1 | tee -a /var/log/docker_build.log
log_success "=== Docker Compose Up Finished ==="

DOMAIN="{{DOMAIN_NAME}}"

if [[ "$DOMAIN" == *"DOMAIN_NAME"* ]]; then
    log_warning "The DOMAIN variable is not set yet"
    exit 0
fi

DROPLET_IP=$(curl -s http://icanhazip.com)
log_info "Droplet IP: $DROPLET_IP"

# Extract base domain for DNS checks (e.g., if DOMAIN is m.superare.com.br, get superare.com.br)
if [[ "$DOMAIN" == m.* ]]; then
    BASE_DOMAIN=$(echo "$DOMAIN" | sed 's/^m\.//')
    log_info "Domain $DOMAIN detected as subdomain of $BASE_DOMAIN"
else
    BASE_DOMAIN="$DOMAIN"
    log_info "Using $DOMAIN as main domain"
fi

log_info "Configuring Nginx for domain: $DOMAIN"

SOURCE_PATH="/var/www/nginx-virtual-host-$DOMAIN"
TARGET_PATH="/etc/nginx/sites-enabled/nginx-virtual-host-$DOMAIN"

# Remove the existing symlink if it exists
if [ -L "$TARGET_PATH" ]; then
    rm $TARGET_PATH
    log_info "Existing symlink for $DOMAIN configuration removed"
fi

# Create a new symlink
ln -s $SOURCE_PATH $TARGET_PATH
log_success "Symlink created for $DOMAIN configuration"

# --- Enforce direct IP blocking in Nginx config ---
NGINX_DEFAULT="/etc/nginx/sites-available/default"

# Backup the original config
sudo cp "$NGINX_DEFAULT" "$NGINX_DEFAULT.bak.$(date +%s)"
log_info "Nginx default config backed up"

# Overwrite with only the blocking server block
echo -e "server {\n    listen 80;\n    server_name _;\n    return 444;\n}" | sudo tee "$NGINX_DEFAULT"
log_info "Direct IP blocking configured in Nginx"

# Test and reload Nginx
if ! nginx -t; then
    log_error "Nginx configuration test failed, stopping the script"
    exit 1
fi

if ! pgrep -x nginx > /dev/null; then
    log_info "Nginx is not running, starting Nginx..."
    systemctl start nginx
    log_success "Nginx started successfully"
else
    log_info "Reloading Nginx to apply new configuration"
    nginx -s reload
    log_success "Nginx reloaded successfully"
fi

log_info "Checking Mautic installation and configuring settings..."
if docker compose exec -T mautic_web test -f /var/www/html/config/local.php && docker compose exec -T mautic_web test -f /var/www/html/config/local.php; then
    # Backup the current configuration before making changes
    log_info "Creating backup of current configuration..."
    BACKUP_FILE="/var/www/html/config/local.php.backup.$(date +%s)"
    docker compose exec -T mautic_web cp /var/www/html/config/local.php "$BACKUP_FILE"
    log_success "Backup created: $BACKUP_FILE"
    
    # Replace the site_url value with the domain
    log_info "Updating site_url in Mautic configuration..."
    OLD_SITE_URL=$(docker compose exec -T mautic_web grep "'site_url'" /var/www/html/config/local.php | sed "s/.*'site_url' => '\([^']*\)'.*/\1/")
    docker compose exec -T mautic_web sed -i "s|'site_url' => '.*',|'site_url' => 'https://$DOMAIN',|g" /var/www/html/config/local.php
    NEW_SITE_URL=$(docker compose exec -T mautic_web grep "'site_url'" /var/www/html/config/local.php | sed "s/.*'site_url' => '\([^']*\)'.*/\1/")
    log_success "Site URL updated: $OLD_SITE_URL → $NEW_SITE_URL"
    
    # Enable Mautic API
    log_info "Configuring Mautic API..."
    
    # Remove old API block if it exists (legacy configuration)
    if docker compose exec -T mautic_web grep -q "'api' => \[" /var/www/html/config/local.php; then
        log_info "Removing old API block structure..."
        docker compose exec -T mautic_web sed -i "/'api' => \[/,/\],/d" /var/www/html/config/local.php
        log_success "Old API block removed"
    fi
    
    if docker compose exec -T mautic_web grep -q "'api_enabled'" /var/www/html/config/local.php; then
        # Update existing API configuration
        log_info "Updating existing API configuration..."
        OLD_API_ENABLED=$(docker compose exec -T mautic_web grep "'api_enabled'" /var/www/html/config/local.php | sed "s/.*'api_enabled' => \(.*\),.*/\1/")
        docker compose exec -T mautic_web sed -i "s/'api_enabled' => false/'api_enabled' => true/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'api_basic_auth_enabled' => false/'api_basic_auth_enabled' => true/g" /var/www/html/config/local.php
        NEW_API_ENABLED=$(docker compose exec -T mautic_web grep "'api_enabled'" /var/www/html/config/local.php | sed "s/.*'api_enabled' => \(.*\),.*/\1/")
        log_success "API enabled: $OLD_API_ENABLED → $NEW_API_ENABLED"
    else
        # Insert new API configuration before the closing );
        log_info "Adding new API configuration..."
        docker compose exec -T mautic_web sed -i "s/);$/'api_enabled' => true,\n    'api_basic_auth_enabled' => true,\n    'api_rate_limiter_enabled' => true,\n    'api_rate_limiter_cache' => 'redis',\n    'api_rate_limiter_limit' => 100,\n    'api_rate_limiter_period' => 60,\n);/" /var/www/html/config/local.php
        log_success "New API configuration added"
    fi
    
    # Configure Mautic Email Settings
    log_info "Configuring Mautic Email Settings..."
    
    # Build the DSN string for SendGrid API (Mautic way)
    if [ -n "$MAUTIC_SENDGRID_API_KEY" ]; then
        MAILER_DSN="sendgrid+api://${MAUTIC_SENDGRID_API_KEY}@default"
        log_info "Using SendGrid API DSN: sendgrid+api://***@default"
    elif [ -n "$MAUTIC_MAILER_DSN" ]; then
        MAILER_DSN="$MAUTIC_MAILER_DSN"
        log_info "Using provided MAILER_DSN: ${MAUTIC_MAILER_DSN//@*/@***}"
    else
        log_warning "No SendGrid API key or MAILER_DSN found!"
        MAILER_DSN="null://null"
    fi
    
    if docker compose exec -T mautic_web grep -q "'mailer_from_name'" /var/www/html/config/local.php; then
        # Update existing mailer configuration
        log_info "Updating existing mailer configuration..."
        OLD_FROM_NAME=$(docker compose exec -T mautic_web grep "'mailer_from_name'" /var/www/html/config/local.php | sed "s/.*'mailer_from_name' => '\([^']*\)'.*/\1/")
        OLD_FROM_EMAIL=$(docker compose exec -T mautic_web grep "'mailer_from_email'" /var/www/html/config/local.php | sed "s/.*'mailer_from_email' => '\([^']*\)'.*/\1/")
        OLD_DSN=$(docker compose exec -T mautic_web grep "'mailer_dsn'" /var/www/html/config/local.php | sed "s/.*'mailer_dsn' => '\([^']*\)'.*/\1/")
        
        docker compose exec -T mautic_web sed -i "s/'mailer_from_name' => '.*'/'mailer_from_name' => '{{MAUTIC_MAILER_FROM_NAME}}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s/'mailer_from_email' => '.*'/'mailer_from_email' => '{{MAUTIC_MAILER_FROM_EMAIL}}'/g" /var/www/html/config/local.php
        docker compose exec -T mautic_web sed -i "s|'mailer_dsn' => '.*'|'mailer_dsn' => '${MAILER_DSN}'|g" /var/www/html/config/local.php
        
        NEW_FROM_NAME=$(docker compose exec -T mautic_web grep "'mailer_from_name'" /var/www/html/config/local.php | sed "s/.*'mailer_from_name' => '\([^']*\)'.*/\1/")
        NEW_FROM_EMAIL=$(docker compose exec -T mautic_web grep "'mailer_from_email'" /var/www/html/config/local.php | sed "s/.*'mailer_from_email' => '\([^']*\)'.*/\1/")
        NEW_DSN=$(docker compose exec -T mautic_web grep "'mailer_dsn'" /var/www/html/config/local.php | sed "s/.*'mailer_dsn' => '\([^']*\)'.*/\1/")
        
        log_success "Mailer configuration updated:"
        log_success "  From Name: $OLD_FROM_NAME → $NEW_FROM_NAME"
        log_success "  From Email: $OLD_FROM_EMAIL → $NEW_FROM_EMAIL"
        log_success "  DSN: ${OLD_DSN//@*/@***} → ${NEW_DSN//@*/@***}"
    else
        # Insert new mailer configuration before the closing );
        log_info "Adding new mailer configuration..."
        docker compose exec -T mautic_web sed -i "s/);$/'mailer_from_name' => '{{MAUTIC_MAILER_FROM_NAME}}',\n    'mailer_from_email' => '{{MAUTIC_MAILER_FROM_EMAIL}}',\n    'mailer_dsn' => '${MAILER_DSN}',\n);/" /var/www/html/config/local.php
        log_success "New mailer configuration added"
    fi
    
    # Verify SendGrid mailer package is installed (should be installed in Dockerfile)
    log_info "Verifying SendGrid mailer package installation..."
    if docker compose exec -T mautic_web composer show symfony/sendgrid-mailer >/dev/null 2>&1; then
        log_success "SendGrid mailer package is already installed (from Dockerfile)"
    else
        log_warning "SendGrid mailer package not found - attempting installation..."
        docker compose exec -T mautic_web composer require symfony/sendgrid-mailer --no-interaction --no-dev --optimize-autoloader
        if [ $? -eq 0 ]; then
            log_success "SendGrid mailer package installed successfully"
        else
            log_error "Failed to install SendGrid mailer package"
        fi
    fi
    
    # Clear Mautic cache
    log_info "Clearing Mautic cache..."
    docker compose exec -T mautic_web php /var/www/html/bin/console cache:clear --env=prod
    log_success "Mautic cache cleared successfully"
    
    # Restart containers to apply configuration changes
    log_info "Restarting containers to apply configuration changes..."
    docker compose restart mautic_web
    log_success "Containers restarted successfully"
    
    # Verify configuration
    log_info "Verifying configuration changes..."
    API_ENABLED=$(docker compose exec -T mautic_web grep "'api_enabled'" /var/www/html/config/local.php | sed "s/.*'api_enabled' => \(.*\),.*/\1/")
    API_AUTH_ENABLED=$(docker compose exec -T mautic_web grep "'api_basic_auth_enabled'" /var/www/html/config/local.php | sed "s/.*'api_basic_auth_enabled' => \(.*\),.*/\1/")
    MAILER_DSN_CONFIGURED=$(docker compose exec -T mautic_web grep "'mailer_dsn'" /var/www/html/config/local.php | sed "s/.*'mailer_dsn' => '\([^']*\)'.*/\1/")
    
    log_success "Configuration verification:"
    log_success "  API Enabled: $API_ENABLED"
    log_success "  API Basic Auth: $API_AUTH_ENABLED"
    log_success "  Mailer DSN: ${MAILER_DSN_CONFIGURED//@*/@***}"
    
    # Test API endpoint
    log_info "Testing API endpoint..."
    sleep 5  # Wait for container to fully restart
    if curl -s -o /dev/null -w "%{http_code}" "http://localhost:${MAUTIC_PORT:-8001}/api/" | grep -q "200\|401"; then
        log_success "API endpoint is responding"
    else
        log_warning "API endpoint test failed"
    fi
    
    # Test SendGrid package installation
    log_info "Testing SendGrid package installation..."
    if docker compose exec -T mautic_web composer show symfony/sendgrid-mailer >/dev/null 2>&1; then
        log_success "SendGrid package is properly installed"
    else
        log_warning "SendGrid package installation verification failed"
    fi
    
else
    log_error "Mautic configuration file not found. Is Mautic installed?"
    exit 1
fi

log_success "=== Script execution completed successfully ==="

# Final summary
log_info "=== Deployment Summary ==="
log_success "✅ Mautic 6 installation and configuration completed"
log_success "✅ API enabled and configured"
log_success "✅ SendGrid email integration configured"
log_success "✅ Nginx configured with domain: $DOMAIN"
log_success "✅ Direct IP blocking enabled"
log_info "=== Deployment Summary Complete ==="
