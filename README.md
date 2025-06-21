# Mautic Docker Deployment

This repository contains the configuration for deploying Mautic on DigitalOcean using Docker Compose.

## Current Configuration

### Domain Setup

- **Domain**: `m.superare.com.br` (hosted on DigitalOcean droplet at `167.71.89.171`)
- **Base Domain**: `superare.com.br` (used for DNS zone lookup)
- **SSL**: Cloudflare Flexible SSL (HTTP between Cloudflare and server)

### Architecture

- **Web Server**: Nginx (port 80)
- **Application**: Mautic (port 8001)
- **Database**: MySQL (Docker container)
- **Proxy**: Nginx → Mautic (localhost:8001)

### DNS Configuration

- `m.superare.com.br` → `167.71.89.171` (DigitalOcean droplet)
- Cloudflare DNS with Flexible SSL mode

## Deployment

### Prerequisites

1. GitHub repository secrets configured:

   - `DIGITALOCEAN_ACCESS_TOKEN`
   - `DIGITALOCEAN_SSH_FINGERPRINT`
   - `MAUTIC_PASSWORD`
   - `SSH_PRIVATE_KEY`
   - `CLOUDFLARE_API_TOKEN` (optional)

2. GitHub repository variables:
   - `DOMAIN`: `m.superare.com.br`
   - `EMAIL_ADDRESS`: Admin email for Mautic

### Deployment Steps

1. Run the GitHub Actions workflow: "Deploy to DigitalOcean"
2. The workflow will:
   - Create DigitalOcean droplet if it doesn't exist
   - Create and attach block storage volumes
   - Update Cloudflare DNS for `m.superare.com.br`
   - Deploy Mautic application
   - Configure Nginx proxy

### Manual Configuration (if needed)

If the deployment doesn't work automatically, you can manually configure nginx:

```bash
# SSH to the droplet
ssh root@167.71.89.171

# Enable the nginx configuration
ln -sf /var/www/nginx-virtual-host-m.superare.com.br /etc/nginx/sites-enabled/nginx-virtual-host-m.superare.com.br

# Test and reload nginx
nginx -t && nginx -s reload
```

## Access

- **Mautic Admin**: http://m.superare.com.br
- **Direct Access**: http://167.71.89.171:8001

## SSL Configuration

Currently using Cloudflare Flexible SSL:

- Users → Cloudflare: HTTPS
- Cloudflare → Server: HTTP

For full SSL, consider:

1. Let's Encrypt certificate
2. Cloudflare Origin Certificate
3. Cloudflare Full SSL mode

## Troubleshooting

1. Check if Mautic is running: `docker ps`
2. Check nginx logs: `tail -f /var/log/nginx/m.superare.com.br_error.log`
3. Check Mautic logs: `docker logs basic-mautic_web-1`
4. Verify DNS: `dig +short m.superare.com.br`
