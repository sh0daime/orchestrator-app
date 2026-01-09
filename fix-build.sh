#!/bin/bash
# Post-build script to fix HTML paths (Mac/Linux version)
# This copies dist/src/home.html to dist/home.html and fixes asset paths for all HTML files

DIST_SRC_HTML="dist/src/home.html"
DIST_HTML="dist/home.html"

if [ -f "$DIST_SRC_HTML" ]; then
    # Copy the file
    cp "$DIST_SRC_HTML" "$DIST_HTML"
    
    # Fix asset paths (replace absolute paths with relative paths)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' 's|src="/assets/|src="./assets/|g' "$DIST_HTML"
        sed -i '' 's|href="/assets/|href="./assets/|g' "$DIST_HTML"
    else
        # Linux
        sed -i 's|src="/assets/|src="./assets/|g' "$DIST_HTML"
        sed -i 's|href="/assets/|href="./assets/|g' "$DIST_HTML"
    fi
    
    echo "Fixed dist/home.html with relative asset paths"
else
    echo "Warning: dist/src/home.html not found"
fi

# Fix settings.html and status.html asset paths (they stay in dist/src/)
for HTML_FILE in "dist/src/settings.html" "dist/src/status.html" "dist/src/index.html"; do
    if [ -f "$HTML_FILE" ]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS - fix paths to reference ../assets/ since these are in src/ subdirectory
            sed -i '' 's|src="/assets/|src="../assets/|g' "$HTML_FILE"
            sed -i '' 's|href="/assets/|href="../assets/|g' "$HTML_FILE"
        else
            # Linux
            sed -i 's|src="/assets/|src="../assets/|g' "$HTML_FILE"
            sed -i 's|href="/assets/|href="../assets/|g' "$HTML_FILE"
        fi
        echo "Fixed $HTML_FILE with relative asset paths"
    fi
done
