@echo off
setlocal EnableDelayedExpansion

REM ============================================================================
REM VCTT Bootstrap Installer
REM This script clones the VCTT repository and runs the full installation
REM For PRIVATE repositories, requires GitHub authentication
REM ============================================================================

echo ============================================================
echo           VCTT Bootstrap Installer
echo ============================================================
echo.

REM Check if git is available
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Git is not installed or not in PATH.
    echo Please install Git for Windows first.
    echo Download from: https://git-scm.com/download/win
    pause
    exit /b 1
)

REM Check if conda is available
where conda >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Conda is not installed or not in PATH.
    echo Please install Anaconda or Miniconda first.
    echo Download from: https://docs.conda.io/en/latest/miniconda.html
    pause
    exit /b 1
)

echo [INFO] Prerequisites check passed.
echo.

REM Check GitHub authentication
echo [STEP 0/3] Checking GitHub authentication...
echo.
echo This repository is PRIVATE and requires GitHub authentication.
echo.
echo You have 3 options:
echo   1. Use GitHub CLI (gh) - Recommended
echo   2. Use Personal Access Token (PAT)
echo   3. Use SSH key
echo.

set "AUTH_METHOD="
set /p AUTH_METHOD="Choose authentication method (1/2/3): "

if "!AUTH_METHOD!"=="1" goto :auth_gh
if "!AUTH_METHOD!"=="2" goto :auth_token
if "!AUTH_METHOD!"=="3" goto :auth_ssh

echo [ERROR] Invalid choice.
pause
exit /b 1

:auth_gh
REM GitHub CLI method
where gh >nul 2>&1
if %ERRORLEVEL% neq 0 goto :gh_not_installed

REM Check if already authenticated
gh auth status >nul 2>&1
if %ERRORLEVEL% neq 0 goto :gh_need_auth

echo [INFO] GitHub CLI authentication successful.
set "REPO_URL=https://github.com/pantheon-lab/data.git"
goto :auth_done

:gh_not_installed
echo.
echo [ERROR] GitHub CLI (gh) is not installed.
echo.
echo Install it from: https://cli.github.com/
echo Or choose a different authentication method.
pause
exit /b 1

:gh_need_auth
echo.
echo [INFO] You need to authenticate with GitHub.
echo A browser window will open for authentication...
echo.
pause
gh auth login
if %ERRORLEVEL% neq 0 goto :gh_auth_failed
echo [INFO] GitHub CLI authentication successful.
set "REPO_URL=https://github.com/pantheon-lab/data.git"
goto :auth_done

:gh_auth_failed
echo [ERROR] GitHub authentication failed.
pause
exit /b 1

:auth_token
REM Personal Access Token method
echo.
echo [INFO] You need a GitHub Personal Access Token (PAT).
echo.
echo If you don't have one:
echo   1. Go to: https://github.com/settings/tokens/new
echo   2. Name: "VCTT Installation"
echo   3. Expiration: 90 days (or as required)
echo   4. Scopes: Check "repo" (Full control of private repositories)
echo   5. Click "Generate token"
echo   6. Copy the token (starts with ghp_...)
echo.

set /p GITHUB_TOKEN="Enter your GitHub Personal Access Token: "
if "!GITHUB_TOKEN!"=="" goto :token_empty

set "REPO_URL=https://!GITHUB_TOKEN!@github.com/pantheon-lab/data.git"
echo [INFO] Will use Personal Access Token for authentication.
goto :auth_done

:token_empty
echo [ERROR] Token cannot be empty.
pause
exit /b 1

:auth_ssh
REM SSH key method
echo.
echo [INFO] Using SSH key authentication.
echo.
echo Make sure:
echo   1. You have generated an SSH key: ssh-keygen -t ed25519 -C "your@email.com"
echo   2. Added it to GitHub: https://github.com/settings/keys
echo   3. Tested connection: ssh -T git@github.com
echo.

REM Test SSH connection
ssh -T git@github.com 2>&1 | findstr /C:"successfully authenticated" >nul
if %ERRORLEVEL% neq 0 goto :ssh_test_failed

set "REPO_URL=git@github.com:pantheon-lab/data.git"
echo [INFO] Will use SSH for authentication.
goto :auth_done

:ssh_test_failed
echo [WARNING] SSH authentication test failed.
echo Make sure your SSH key is added to GitHub.
set /p CONTINUE="Continue anyway? (y/N): "
if /i not "!CONTINUE!"=="y" exit /b 1
set "REPO_URL=git@github.com:pantheon-lab/data.git"
echo [INFO] Will use SSH for authentication.
goto :auth_done

:auth_done

echo.

REM Ask for installation directory
set "DEFAULT_DIR=%USERPROFILE%\VCTT"
set /p INSTALL_DIR="Installation directory [%DEFAULT_DIR%]: "
if "!INSTALL_DIR!"=="" set "INSTALL_DIR=%DEFAULT_DIR%"

echo.
echo [INFO] Will install to: !INSTALL_DIR!
echo.

REM Check if directory already exists
if exist "!INSTALL_DIR!\VCTT_app" (
    echo [WARNING] VCTT appears to be already installed at this location.
    set /p REINSTALL="Reinstall? This will delete the existing installation (y/N): "
    if /i not "!REINSTALL!"=="y" (
        echo Installation cancelled.
        pause
        exit /b 0
    )
    echo [INFO] Removing existing installation...
    rmdir /s /q "!INSTALL_DIR!"
)

REM Create parent directory
if not exist "!INSTALL_DIR!" (
    mkdir "!INSTALL_DIR!"
)

REM Clone repository
echo.
echo [STEP 1/3] Cloning VCTT repository...
echo This may take a few minutes depending on your internet connection...
echo.

git clone -b calvin/vtcc_update !REPO_URL! "!INSTALL_DIR!"
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Failed to clone repository.
    echo.
    echo Common issues:
    echo   - Invalid credentials
    echo   - No access to private repository
    echo   - Network/firewall issues
    echo   - Branch 'calvin/vtcc_update' does not exist
    echo.
    echo Please check:
    echo   1. Your GitHub authentication is valid
    echo   2. You have access to pantheon-lab/data repository
    echo   3. Your internet connection
    echo   4. The branch 'calvin/vtcc_update' exists
    echo.
    pause
    exit /b 1
)

echo.
echo [INFO] Repository cloned successfully.

REM Initialize submodules
echo.
echo [STEP 2/3] Initializing library submodule...
cd /d "!INSTALL_DIR!"
git submodule update --init library
if %ERRORLEVEL% neq 0 (
    echo [WARNING] Failed to initialize submodule.
    echo This may cause issues. Continue anyway.
)

REM Run the main installer
echo.
echo [STEP 3/3] Running VCTT installation...
echo.

if not exist "!INSTALL_DIR!\VCTT_app" (
    echo [ERROR] VCTT_app directory not found at: !INSTALL_DIR!\VCTT_app
    echo The repository may not have cloned correctly.
    pause
    exit /b 1
)

cd /d "!INSTALL_DIR!\VCTT_app"
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to change to VCTT_app directory
    pause
    exit /b 1
)

if not exist "install_vctt.bat" (
    echo [ERROR] install_vctt.bat not found in: !INSTALL_DIR!\VCTT_app
    echo Current directory: %CD%
    echo Directory contents:
    dir /b
    pause
    exit /b 1
)

call install_vctt.bat

if %ERRORLEVEL% equ 0 (
    echo.
    echo ============================================================
    echo           Bootstrap Complete!
    echo ============================================================
    echo.
    echo VCTT has been installed to: !INSTALL_DIR!
    echo.
    echo To launch VCTT:
    echo   1. Navigate to: !INSTALL_DIR!\VCTT_app
    echo   2. Double-click: launch_vctt.bat
    echo.
    echo Or create a desktop shortcut to launch_vctt.bat
    echo.
) else (
    echo.
    echo [ERROR] Installation failed. Check errors above.
    echo.
)

pause
