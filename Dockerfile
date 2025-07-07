# Define the Mautic version as an argument
ARG MAUTIC_VERSION=5.2.3-apache

# Build stage:
FROM mautic/mautic:${MAUTIC_VERSION} AS build

# Install dependencies needed for Composer to run and rebuild assets:
RUN apt-get update && apt-get install -y git curl npm && rm -rf /var/lib/apt/lists/*

# Install Composer globally:
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Install any Mautic theme or plugin using Composer:
RUN cd /var/www/html && \
    COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_PROCESS_TIMEOUT=10000  vendor/bin/composer require chimpino/theme-air:^1.0 --no-scripts --no-interaction

# Production stage:
FROM mautic/mautic:${MAUTIC_VERSION}

# Install Composer globally in the production image
RUN apt-get update && apt-get install -y curl && \
    curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Copy the built assets and the Mautic installation from the build stage:
COPY --from=build --chown=www-data:www-data /var/www/html /var/www/html

# Install SendGrid mailer bridge in production stage using global composer
RUN cd /var/www/html && \
    COMPOSER_ALLOW_SUPERUSER=1 COMPOSER_PROCESS_TIMEOUT=10000 composer require symfony/sendgrid-mailer --no-scripts --no-interaction --optimize-autoloader

# Copy security .htaccess file
COPY .htaccess /var/www/html/.htaccess
