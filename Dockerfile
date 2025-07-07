# Use the official Mautic 6 image (built on PHP 8.2+)
FROM mautic/mautic:6.0.3-apache

# Install git (if not already present in the image)
RUN apt-get update && apt-get install -y git

# Install the SendGrid mailer bridge
RUN cd /var/www/html && \
    COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_PROCESS_TIMEOUT=10000 composer require symfony/sendgrid-mailer --no-scripts --no-interaction --optimize-autoloader

# (Optional) Install any custom themes or plugins here
# RUN cd /var/www/html && \
#     COMPOSER_ALLOW_SUPERUSER=1 composer require your/plugin-or-theme --no-scripts --no-interaction

# Copy security .htaccess file if you have a custom one
COPY .htaccess /var/www/html/.htaccess
