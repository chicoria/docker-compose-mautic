# Environment Variables for Mautic Setup

## Required Environment Variables

### Email Configuration (SendGrid)

```bash
# Option 1: Using SendGrid API Key (Recommended)
MAUTIC_SENDGRID_API_KEY=your_sendgrid_api_key_here

# Option 2: Using Full DSN
MAUTIC_MAILER_DSN=sendgrid+api://your_api_key@default

# Email Sender Information
MAUTIC_MAILER_FROM_NAME="Your Company Name"
MAUTIC_MAILER_FROM_EMAIL="noreply@yourdomain.com"
```

### Database Configuration

```bash
MYSQL_ROOT_PASSWORD=your_mysql_root_password
MYSQL_DATABASE=mautic
MYSQL_USER=mautic
MYSQL_PASSWORD=your_mysql_password
```

### Mautic Installation

```bash
EMAIL_ADDRESS=admin@yourdomain.com
MAUTIC_PASSWORD=your_admin_password
IP_ADDRESS=your_server_ip
PORT=8001
DOMAIN_NAME=yourdomain.com
```

## How to Set Environment Variables

### Option 1: Using .mautic_env file

Create a `.mautic_env` file in the project root with the variables above.

### Option 2: Using GitHub Actions Secrets

For automated deployments, set these as secrets in your GitHub repository.

## Troubleshooting

### Missing SendGrid Configuration

If you see warnings about missing SendGrid configuration:

1. Set `MAUTIC_SENDGRID_API_KEY` or `MAUTIC_MAILER_DSN`
2. The system will use `null://null` transport (emails won't be sent)
3. You can configure email later in Mautic admin panel

### Sed Command Errors

If you see sed errors during configuration:

1. Check for special characters in your DSN strings
2. Ensure environment variables are properly set
3. The script now handles escaping automatically
