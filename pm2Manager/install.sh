#!/bin/bash
# PM2 Manager Plugin Installation Script
# Author: Master3395

echo "Installing PM2 Manager Plugin..."

# Check if PM2 is installed
if ! command -v pm2 &> /dev/null; then
    echo "Warning: PM2 is not installed. Please install PM2 first:"
    echo "  npm install -g pm2"
    echo ""
    echo "Continuing with installation..."
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "Warning: Node.js is not installed. PM2 Manager requires Node.js."
    echo "Please install Node.js first."
    exit 1
fi

echo "PM2 Manager plugin installation completed!"
echo "Please restart CyberPanel service: systemctl restart lscpd"
