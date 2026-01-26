#!/bin/bash
# Package Google Tag Manager Plugin for CyberPanel
# Author: master3395

PLUGIN_NAME="googleTagManager"
PLUGIN_DIR="/home/cyberpanel-plugins/${PLUGIN_NAME}"
PACKAGE_NAME="${PLUGIN_NAME}.zip"

echo "Packaging Google Tag Manager Plugin..."

# Change to plugin directory
cd "$PLUGIN_DIR" || exit 1

# Remove any existing package
rm -f "${PACKAGE_NAME}"

# Create ZIP file excluding unnecessary files
zip -r "${PACKAGE_NAME}" . \
    -x "*.pyc" \
    -x "*.pyo" \
    -x "__pycache__/*" \
    -x "*.log" \
    -x ".git/*" \
    -x ".gitignore" \
    -x "package.sh" \
    -x "*.zip"

echo "Package created: ${PLUGIN_DIR}/${PACKAGE_NAME}"
echo "File size: $(du -h "${PACKAGE_NAME}" | cut -f1)"
