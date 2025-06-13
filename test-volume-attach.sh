#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Testing Volume Attachment Process${NC}"
echo "----------------------------------------"

# Check if doctl is installed
if ! command -v doctl &> /dev/null; then
    echo -e "${RED}Error: doctl is not installed${NC}"
    exit 1
fi

# Get droplet ID
echo -e "\n${YELLOW}Getting Droplet ID...${NC}"
DROPLET_ID=$(doctl compute droplet list --format ID,Name --no-header | grep mautic-vps | awk '{print $1}')

if [ -z "$DROPLET_ID" ]; then
    echo -e "${RED}Error: Droplet 'mautic-vps' not found${NC}"
    exit 1
fi
echo -e "${GREEN}Found Droplet ID: $DROPLET_ID${NC}"

# Get volume IDs
echo -e "\n${YELLOW}Getting Volume IDs...${NC}"

# MySQL Volume
echo "Checking MySQL volume..."
MYSQL_VOLUME_ID=$(doctl compute volume list --format ID,Name --no-header | grep mautic-mysql | awk '{print $1}')
if [ -z "$MYSQL_VOLUME_ID" ]; then
    echo -e "${RED}MySQL volume not found${NC}"
else
    echo -e "${GREEN}Found MySQL Volume ID: $MYSQL_VOLUME_ID${NC}"
fi

# Files Volume
echo "Checking Files volume..."
FILES_VOLUME_ID=$(doctl compute volume list --format ID,Name --no-header | grep mautic-files | awk '{print $1}')
if [ -z "$FILES_VOLUME_ID" ]; then
    echo -e "${RED}Files volume not found${NC}"
else
    echo -e "${GREEN}Found Files Volume ID: $FILES_VOLUME_ID${NC}"
fi

# Attach volumes
echo -e "\n${YELLOW}Attaching Volumes...${NC}"

# MySQL Volume
if [ -n "$MYSQL_VOLUME_ID" ]; then
    echo "Attaching MySQL volume..."
    if doctl compute volume-action attach "$MYSQL_VOLUME_ID" --droplet-id "$DROPLET_ID"; then
        echo -e "${GREEN}MySQL volume attached successfully${NC}"
    else
        echo -e "${RED}Failed to attach MySQL volume${NC}"
    fi
fi

# Files Volume
if [ -n "$FILES_VOLUME_ID" ]; then
    echo "Attaching Files volume..."
    if doctl compute volume-action attach "$FILES_VOLUME_ID" --droplet-id "$DROPLET_ID"; then
        echo -e "${GREEN}Files volume attached successfully${NC}"
    else
        echo -e "${RED}Failed to attach Files volume${NC}"
    fi
fi

# Verify attachments
echo -e "\n${YELLOW}Verifying Volume Attachments...${NC}"
echo "Checking droplet volumes..."
doctl compute droplet get $DROPLET_ID --format Volumes

echo -e "\n${YELLOW}Process Complete${NC}"
echo "----------------------------------------" 