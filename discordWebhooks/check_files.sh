#!/bin/bash
echo "Checking files..."
for file in utils.py views.py urls.py meta.xml; do
    if [ -f "$file" ]; then
        echo "✓ $file exists"
    else
        echo "✗ $file missing"
    fi
done
