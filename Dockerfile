FROM mautic/mautic:5.0.4-apache

# Install git for composer
RUN apt-get update && apt-get install -y git

# Copy .htaccess for security
COPY .htaccess /var/www/html/.htaccess
