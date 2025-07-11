#!/bin/bash

# Create a swap file
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
sudo sysctl vm.swappiness=10
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# Enable ports for HTTP traffic
sudo ufw allow 80
sudo ufw allow 443

# Allow outbound SMTP traffic
sudo ufw allow out 587/tcp

# Block direct IP access to Mautic (only allow domain-based access)
# This will block direct access to port 8001 from external IPs
# sudo ufw deny 8001

# Install Nginx
sudo apt-get update
sudo apt-get install -y nginx vim nano

# Create mount points for DigitalOcean Block Storage
sudo mkdir -p /mnt/do-volume
sudo mkdir -p /mnt/do-volume/mysql
sudo mkdir -p /mnt/do-volume/mautic/config
sudo mkdir -p /mnt/do-volume/mautic/logs
sudo mkdir -p /mnt/do-volume/mautic/media/files
sudo mkdir -p /mnt/do-volume/mautic/media/images
sudo mkdir -p /mnt/do-volume/cron

# Set proper permissions
sudo chown -R 1000:1000 /mnt/do-volume/mautic
sudo chown -R 999:999 /mnt/do-volume/mysql

# Create SSL directory for Cloudflare
sudo mkdir -p /etc/nginx/ssl
sudo chmod 700 /etc/nginx/ssl


