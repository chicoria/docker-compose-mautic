# Site Deployment to Cloudflare Pages

This document explains how to deploy the site files to Cloudflare Pages for `superare.com.br`.

## Overview

The site deployment workflow automatically deploys HTML files from the `site/` folder to Cloudflare Pages whenever:

- Files in the `site/` folder are modified and pushed to the main branch
- The workflow is manually triggered

## Prerequisites

### 1. Cloudflare Pages Project Setup

First, create a Cloudflare Pages project:

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Navigate to **Pages** → **Create a project**
3. Choose **Direct Upload** (we'll use API deployment)
4. Set project name to: `superare`
5. Set production branch to: `main`
6. Complete the project creation

### 2. GitHub Secrets Configuration

Add these secrets to your GitHub repository:

1. Go to your repository → **Settings** → **Secrets and variables** → **Actions**
2. Add the following secrets:

#### Required Secrets:

- **`CLOUDFLARE_API_TOKEN`**

  - Go to [Cloudflare API Tokens](https://dash.cloudflare.com/profile/api-tokens)
  - Create a new token with these permissions:
    - **Account**: Cloudflare Pages (Read, Write)
    - **Zone**: DNS (Read, Write) - for the domain
  - Copy the token value

- **`CLOUDFLARE_ACCOUNT_ID`**
  - Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
  - Look at the URL or go to **Account Home** → **Account ID**
  - Copy the 32-character Account ID

## Workflow Files

Two deployment workflows are available:

### 1. `deploy-pages.yml` (Wrangler CLI)

- Uses Cloudflare's Wrangler CLI
- More features and better integration
- Requires Wrangler CLI setup

### 2. `deploy-pages-simple.yml` (Direct API)

- Uses Cloudflare API directly
- Simpler and more reliable
- **Recommended for most users**

## Usage

### Automatic Deployment

The workflow runs automatically when:

- Files in the `site/` folder are modified
- Changes are pushed to the `main` branch

### Manual Deployment

1. Go to **Actions** tab in your GitHub repository
2. Select **"Deploy Site to Cloudflare Pages (Simple)"**
3. Click **"Run workflow"**
4. Choose environment (production)
5. Click **"Run workflow"**

## File Structure

```
docker-compose-mautic/
├── site/
│   ├── index.html          # Main homepage
│   └── obrigado-interesse.html  # Thank you page
├── .github/workflows/
│   ├── deploy-pages.yml
│   └── deploy-pages-simple.yml
└── SITE-DEPLOYMENT.md
```

## Deployment Process

1. **Check Secrets**: Validates required Cloudflare credentials
2. **Create Package**: Zips the `site/` folder contents
3. **Find Project**: Locates the Cloudflare Pages project
4. **Create Deployment**: Initiates a new deployment
5. **Upload Files**: Uploads the site files
6. **Wait & Verify**: Checks deployment status and site accessibility

## Monitoring

- **GitHub Actions**: Check the Actions tab for deployment logs
- **Cloudflare Dashboard**: Monitor at https://dash.cloudflare.com/pages
- **Site URL**: https://superare.com.br

## Troubleshooting

### Common Issues:

1. **"Could not find Cloudflare Pages project 'superare'"**

   - Ensure the project name is exactly `superare` in Cloudflare Pages
   - Check that the project exists in your account

2. **"Missing CLOUDFLARE_API_TOKEN"**

   - Verify the API token is added to GitHub secrets
   - Ensure the token has Pages permissions

3. **"Missing CLOUDFLARE_ACCOUNT_ID"**

   - Verify the Account ID is correct
   - Check that it's a 32-character string

4. **Site not accessible after deployment**
   - Wait a few minutes for DNS propagation
   - Check Cloudflare Pages dashboard for deployment status
   - Verify the custom domain is configured in Pages settings

### Custom Domain Setup

If `superare.com.br` is not automatically configured:

1. Go to Cloudflare Pages dashboard
2. Select the `superare` project
3. Go to **Custom domains**
4. Add `superare.com.br`
5. Ensure DNS is configured (CNAME record)

## Security Headers

The deployment automatically adds security headers:

- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`
- `Referrer-Policy: strict-origin-when-cross-origin`

## Next Steps

After successful deployment:

1. Test the site at https://superare.com.br
2. Verify all pages load correctly
3. Check that forms and links work properly
4. Monitor performance in Cloudflare Analytics
