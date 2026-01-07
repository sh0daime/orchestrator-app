#!/bin/bash
# ============================================================================
# VCTT Bootstrap Installer (Mac/Linux)
# This script clones the VCTT repository and runs the full installation
# For PRIVATE repositories, requires GitHub authentication
# ============================================================================

set -e  # Exit on error

echo "============================================================"
echo "           VCTT Bootstrap Installer"
echo "============================================================"
echo

# Check if git is available
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git is not installed or not in PATH."
    echo "Please install Git first."
    echo "macOS: brew install git"
    echo "Linux: sudo apt-get install git (Ubuntu/Debian) or sudo yum install git (RHEL/CentOS)"
    exit 1
fi

# Check if conda is available
if ! command -v conda &> /dev/null; then
    echo "[ERROR] Conda is not installed or not in PATH."
    echo "Please install Anaconda or Miniconda first."
    echo "Download from: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
fi

echo "[INFO] Prerequisites check passed."
echo

# Check GitHub authentication
echo "[STEP 0/3] Checking GitHub authentication..."
echo
echo "This repository is PRIVATE and requires GitHub authentication."
echo
echo "You have 3 options:"
echo "  1. Use GitHub CLI (gh) - Recommended"
echo "  2. Use Personal Access Token (PAT)"
echo "  3. Use SSH key"
echo

read -p "Choose authentication method (1/2/3): " AUTH_METHOD

case "$AUTH_METHOD" in
    1)
        # GitHub CLI method
        if ! command -v gh &> /dev/null; then
            echo
            echo "[ERROR] GitHub CLI (gh) is not installed."
            echo
            echo "Install it from: https://cli.github.com/"
            echo "Or choose a different authentication method."
            exit 1
        fi
        
        # Check if already authenticated
        if ! gh auth status &> /dev/null; then
            echo
            echo "[INFO] You need to authenticate with GitHub."
            echo "A browser window will open for authentication..."
            echo
            read -p "Press Enter to continue..."
            gh auth login
            if [ $? -ne 0 ]; then
                echo "[ERROR] GitHub authentication failed."
                exit 1
            fi
        fi
        
        echo "[INFO] GitHub CLI authentication successful."
        REPO_URL="https://github.com/pantheon-lab/data.git"
        ;;
    2)
        # Personal Access Token method
        echo
        echo "[INFO] You need a GitHub Personal Access Token (PAT)."
        echo
        echo "If you don't have one:"
        echo "  1. Go to: https://github.com/settings/tokens/new"
        echo "  2. Name: \"VCTT Installation\""
        echo "  3. Expiration: 90 days (or as required)"
        echo "  4. Scopes: Check \"repo\" (Full control of private repositories)"
        echo "  5. Click \"Generate token\""
        echo "  6. Copy the token (starts with ghp_...)"
        echo
        
        read -p "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
        if [ -z "$GITHUB_TOKEN" ]; then
            echo "[ERROR] Token cannot be empty."
            exit 1
        fi
        
        REPO_URL="https://${GITHUB_TOKEN}@github.com/pantheon-lab/data.git"
        echo "[INFO] Will use Personal Access Token for authentication."
        ;;
    3)
        # SSH key method
        echo
        echo "[INFO] Using SSH key authentication."
        echo
        echo "Make sure:"
        echo "  1. You have generated an SSH key: ssh-keygen -t ed25519 -C \"your@email.com\""
        echo "  2. Added it to GitHub: https://github.com/settings/keys"
        echo "  3. Tested connection: ssh -T git@github.com"
        echo
        
        # Test SSH connection
        if ssh -T git@github.com 2>&1 | grep -q "successfully authenticated"; then
            REPO_URL="git@github.com:pantheon-lab/data.git"
            echo "[INFO] Will use SSH for authentication."
        else
            echo "[WARNING] SSH authentication test failed."
            echo "Make sure your SSH key is added to GitHub."
            read -p "Continue anyway? (y/N): " CONTINUE
            if [ "$CONTINUE" != "y" ] && [ "$CONTINUE" != "Y" ]; then
                exit 1
            fi
            REPO_URL="git@github.com:pantheon-lab/data.git"
            echo "[INFO] Will use SSH for authentication."
        fi
        ;;
    *)
        echo "[ERROR] Invalid choice."
        exit 1
        ;;
esac

echo

# Check if installation directory was provided as command-line argument
if [ -z "$1" ]; then
    # No argument provided, prompt user
    DEFAULT_DIR="$HOME/VCTT"
    read -p "Installation directory [$DEFAULT_DIR]: " INSTALL_DIR
    INSTALL_DIR="${INSTALL_DIR:-$DEFAULT_DIR}"
else
    # Use provided directory
    INSTALL_DIR="$1"
    echo "[INFO] Using installation directory from command line: $INSTALL_DIR"
fi

echo
echo "[INFO] Will install to: $INSTALL_DIR"
echo

# Check if VCTT_app already exists at this location
if [ -d "$INSTALL_DIR/VCTT_app" ]; then
    echo "[WARNING] VCTT appears to be already installed at this location."
    read -p "Reinstall? This will delete the existing installation (y/N): " REINSTALL
    if [ "$REINSTALL" != "y" ] && [ "$REINSTALL" != "Y" ]; then
        echo "Installation cancelled."
        exit 0
    fi
    echo "[INFO] Removing existing installation..."
    rm -rf "$INSTALL_DIR"
fi

# Create parent directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Check if directory is not empty (excluding hidden files)
if [ -d "$INSTALL_DIR" ] && [ "$(ls -A "$INSTALL_DIR" 2>/dev/null)" ]; then
    if [ ! -d "$INSTALL_DIR/VCTT_app" ]; then
        echo "[WARNING] Directory $INSTALL_DIR already exists and is not empty."
        echo "[INFO] Contents will be preserved, VCTT will be cloned into this directory."
        read -p "Press Enter to continue..."
    fi
fi

# Clone repository
echo
echo "[STEP 1/3] Cloning VCTT repository..."
echo "This may take a few minutes depending on your internet connection..."
echo

git clone -b calvin/vtcc_update "$REPO_URL" "$INSTALL_DIR"
if [ $? -ne 0 ]; then
    echo
    echo "[ERROR] Failed to clone repository."
    echo
    echo "Common issues:"
    echo "  - Invalid credentials"
    echo "  - No access to private repository"
    echo "  - Network/firewall issues"
    echo "  - Branch 'calvin/vtcc_update' does not exist"
    echo
    echo "Please check:"
    echo "  1. Your GitHub authentication is valid"
    echo "  2. You have access to pantheon-lab/data repository"
    echo "  3. Your internet connection"
    echo "  4. The branch 'calvin/vtcc_update' exists"
    echo
    exit 1
fi

echo
echo "[INFO] Repository cloned successfully."

# Initialize submodules
echo
echo "[STEP 2/3] Initializing library submodule..."
cd "$INSTALL_DIR"
git submodule update --init library
if [ $? -ne 0 ]; then
    echo "[WARNING] Failed to initialize submodule."
    echo "This may cause issues. Continue anyway."
fi

# Run the main installer
echo
echo "[STEP 3/3] Running VCTT installation..."
echo

if [ ! -d "$INSTALL_DIR/VCTT_app" ]; then
    echo "[ERROR] VCTT_app directory not found at: $INSTALL_DIR/VCTT_app"
    echo "The repository may not have cloned correctly."
    exit 1
fi

cd "$INSTALL_DIR/VCTT_app"
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to change to VCTT_app directory"
    exit 1
fi

if [ ! -f "install_vctt.sh" ]; then
    echo "[ERROR] install_vctt.sh not found in: $INSTALL_DIR/VCTT_app"
    echo "Current directory: $(pwd)"
    echo "Directory contents:"
    ls -la
    exit 1
fi

bash install_vctt.sh

if [ $? -eq 0 ]; then
    echo
    echo "============================================================"
    echo "           Bootstrap Complete!"
    echo "============================================================"
    echo
    echo "VCTT has been installed to: $INSTALL_DIR"
    echo
    echo "To launch VCTT:"
    echo "  1. Navigate to: $INSTALL_DIR/VCTT_app"
    echo "  2. Run: bash launch_vctt.sh"
    echo
    echo "Or create a desktop shortcut to launch_vctt.sh"
    echo
else
    echo
    echo "[ERROR] Installation failed. Check errors above."
    echo
fi

