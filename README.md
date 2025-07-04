# Mautic Docker Deployment

This repository contains a comprehensive configuration for deploying Mautic on DigitalOcean using Docker Compose with automated SSL, security hardening, and form integration.

## Current Configuration

### Domain Setup

- **Main Domain**: `superare.com.br` (used for DNS zone lookup)
- **Mautic Subdomain**: `m.superare.com.br` (hosted on DigitalOcean droplet at `167.71.89.171`)
- **SSL**: Let's Encrypt certificates with automatic renewal
- **Security**: Comprehensive nginx security rules protecting sensitive files

### Architecture

- **CDN & DNS**: Cloudflare (DNS management, CDN caching, SSL proxy)
- **Web Server**: Nginx (port 80/443) with SSL termination
- **Application**: Mautic (port 8001)
- **Database**: MySQL (Docker container with persistent volume)
- **Storage**: DigitalOcean Block Storage for data persistence
- **Proxy Chain**: Cloudflare → Nginx → Mautic (localhost:8001)
- **SSL**: Let's Encrypt certificates managed by Certbot

**Traffic Flow**:

1. **Users** → **Cloudflare** (HTTPS, DNS resolution, CDN caching)
2. **Cloudflare** → **DigitalOcean Droplet** (HTTPS, Let's Encrypt certificates)
3. **Nginx** → **Mautic Container** (HTTP, localhost:8001)
4. **Mautic** → **MySQL Container** (Database queries)

### Security Features

The deployment includes comprehensive security measures:

- **File Protection**: Blocks access to sensitive files (`.env`, `.git`, `composer.json`, etc.)
- **Documentation Protection**: Blocks access to README, LICENSE, and documentation files
- **Backup Protection**: Blocks access to backup and temporary files
- **Log Protection**: Blocks access to log files
- **CORS Configuration**: Properly configured for cross-origin form submissions

### Form Integration

- **Contact Form**: Integrated form on main domain (`superare.com.br`) that submits to Mautic
- **CORS Handling**: Properly configured for cross-domain form submissions
- **Field Mapping**: Supports custom contact fields (country code, profession)
- **API Integration**: Mautic API enabled for programmatic access

## Nginx Direct IP Blocking (DRY Approach)

- **Direct IP blocking is handled globally** in `/etc/nginx/sites-available/default`.
- The deployment script (`setup-dc.sh`) ensures that any HTTP request to the server's IP (or unknown hostnames) is immediately closed with a 444 status, preventing direct access.
- **Domain-specific Nginx configs** (from `nginx-virtual-host-template`) do not include a direct IP blocking block—this keeps configuration DRY and avoids redundancy.
- All security rules for sensitive files, CORS, etc., are defined in the domain-specific server block only.

## Deployment

### Prerequisites

1. **GitHub Repository Secrets**:

   - `DIGITALOCEAN_ACCESS_TOKEN`
   - `DIGITALOCEAN_SSH_FINGERPRINT`
   - `MAUTIC_PASSWORD`
   - `SSH_PRIVATE_KEY`
   - `CLOUDFLARE_API_TOKEN` (optional, for DNS management)

2. **GitHub Repository Variables**:
   - `DOMAIN`: `superare.com.br` (main domain)
   - `EMAIL_ADDRESS`: Admin email for Mautic and SSL notifications

### Automated Deployment

1. **Run the GitHub Actions workflow**: "Deploy to DigitalOcean"
2. **The workflow will automatically**:
   - Create DigitalOcean droplet if it doesn't exist
   - Create and attach block storage volumes (MySQL + Mautic files)
   - Update Cloudflare DNS for `m.superare.com.br`
   - Deploy Mautic application with Docker Compose
   - Configure Nginx proxy with security rules
   - **Install Let's Encrypt SSL certificates**
   - **Configure HTTPS with automatic redirects**
   - Enable Mautic API for integration
   - Apply comprehensive security hardening

### What Gets Deployed

- ✅ **Mautic Application**: Latest version with persistent storage
- ✅ **SSL Certificates**: Automatic Let's Encrypt setup
- ✅ **Security Hardening**: Comprehensive nginx security rules
- ✅ **CORS Configuration**: Cross-origin form submission support
- ✅ **API Access**: Mautic API enabled with Basic Auth
- ✅ **Monitoring**: Health checks and logging
- ✅ **Backup Strategy**: Persistent volumes for data protection

## Access

- **Mautic Admin**: https://m.superare.com.br
- **Direct Access**: http://167.71.89.171:8001 (HTTP only, for debugging)

## SSL Configuration

**Fully Automated Let's Encrypt Setup**:

- ✅ **Automatic Certificate Generation**: Certbot integration in deployment
- ✅ **Automatic Renewal**: Certbot cron jobs for certificate renewal
- ✅ **HTTP to HTTPS Redirects**: Automatic redirect configuration
- ✅ **Email Notifications**: SSL expiration notifications

**SSL Chain**:

- Users → Cloudflare: HTTPS
- Cloudflare → Server: HTTPS (Let's Encrypt certificates)

## Form Integration

### Frontend Form

- **Location**: Main domain (`superare.com.br`)
- **Submission**: Cross-domain to `m.superare.com.br`
- **Fields**: Name, email, phone, country code, profession
- **CORS**: Properly configured for cross-origin requests

### Backend Processing

- **Mautic Integration**: Form submissions create contacts
- **Custom Fields**: Support for country code and profession
- **API Access**: Programmatic contact management
- **Error Handling**: Comprehensive logging and error reporting

## Security Features

### Nginx Security Rules

```nginx
# Environment files
location ~ /\.env(\.example|\.local|\.production)?$ { deny all; }

# Git files
location ~ /\.git { deny all; }

# Composer files
location ~ /composer\.(json|lock)$ { deny all; }

# Documentation files
location ~ /(README|CHANGELOG|LICENSE|\.md)$ { deny all; }

# Backup and temporary files
location ~ /\.(bak|backup|tmp|temp|swp|swo)$ { deny all; }

# Log files
location ~ /\.(log|txt)$ { deny all; }
```

### Additional Security

- **CORS Headers**: Properly configured for legitimate cross-origin requests
- **API Security**: Basic authentication for Mautic API
- **File Permissions**: Secure file permissions on sensitive directories
- **Docker Security**: Non-root containers and security best practices

## Troubleshooting

### Quick Diagnostics

```bash
# Check if Mautic is running
docker ps

# Check nginx configuration
nginx -t

# Check nginx logs
tail -f /var/log/nginx/m.superare.com.br_error.log

# Check Mautic logs
docker logs basic-mautic_web-1

# Test SSL certificate
curl -I https://m.superare.com.br

# Verify DNS
dig +short m.superare.com.br
```

### Common Issues

1. **SSL Certificate Issues**:

   ```bash
   # Check certificate status
   certbot certificates

   # Renew certificates manually
   certbot renew
   ```

2. **Form Submission Issues**:

   - Check CORS headers in browser developer tools
   - Verify form field names match Mautic expectations
   - Check nginx error logs for CORS issues

3. **API Access Issues**:
   - Verify API is enabled in Mautic settings
   - Check Basic Auth credentials
   - Test API endpoints with curl

### Log Locations

- **Nginx Access Logs**: `/var/log/nginx/m.superare.com.br_access.log`
- **Nginx Error Logs**: `/var/log/nginx/m.superare.com.br_error.log`
- **Mautic Logs**: `docker logs basic-mautic_web-1`
- **SSL Logs**: `/var/log/letsencrypt/`

## Maintenance

### SSL Certificate Renewal

Certificates are automatically renewed by Certbot cron jobs. Manual renewal:

```bash
certbot renew --dry-run  # Test renewal
certbot renew            # Actual renewal
```

### Security Updates

The deployment includes automatic security patches. Manual security updates:

```bash
# Update nginx security rules
./nginx-security-patch-safe.sh

# Check for security vulnerabilities
docker scan basic-mautic_web-1
```

### Backup Strategy

- **Database**: MySQL data stored in persistent volume
- **Files**: Mautic files stored in persistent volume
- **Configuration**: Nginx and SSL configs backed up automatically

## Development

### Local Development

```bash
# Clone repository
git clone <repository-url>
cd docker-compose-mautic

# Set up environment
cp .mautic_env.example .mautic_env
# Edit .mautic_env with your settings

# Run locally
docker-compose up -d
```

### Customization

- **Form Fields**: Modify `create_mautic_form.py` for custom field creation
- **Security Rules**: Update `nginx-virtual-host-template` for custom security
- **SSL Configuration**: Modify Certbot parameters in deployment workflow

## Support

For issues and questions:

1. Check the troubleshooting section above
2. Review GitHub Actions logs for deployment issues
3. Check server logs for runtime issues
4. Verify DNS and SSL certificate status

## Post-Installation Workflows

After deploying Mautic, there are now two separate post-installation workflows for configuration and data setup:

### 1. Post-Installation Configuration

**Workflow:** `.github/workflows/post-install-configuration.yml`

- Configures email server (SendGrid) and tests email delivery
- Uses secrets/variables: `SENDGRID_API_KEY`, `EMAIL_ADDRESS`, `MOBILE_NUMBER`
- Sends a test email to verify configuration
- Should be run after the main deployment and before sending any campaign emails

### 2. Post-Installation Pre-Configured Data

**Workflow:** `.github/workflows/post-install-pre-configured-data.yml`

- Creates Mautic forms, campaigns, custom fields, tags, and 3-day welcome email sequence
- Uses secrets/variables: `MAUTIC_PASSWORD`, `EMAIL_ADDRESS`
- Sets up all automation and data structures for lead capture and nurturing
- Should be run after the main deployment and before launching your marketing campaigns

### How to Use

1. **Deploy to DigitalOcean** using the main deployment workflow
2. **Run `Post-Installation Pre-Configured Data`** to set up forms, campaigns, and automation
3. **Run `Post-Installation Configuration`** to set up and test SendGrid email delivery
4. **Test your form and email automation**

**Note:** You can re-run either workflow independently if you need to update email settings or re-create forms/campaigns.
