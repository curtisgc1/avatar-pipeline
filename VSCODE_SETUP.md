# VS Code Setup and Troubleshooting Guide

## Overview
This document provides setup instructions and troubleshooting steps for Visual Studio Code when working with the Avatar Pipeline project.

## Required Extensions

The following VS Code extensions are recommended for this project:

- **GitHub Copilot** (`github.copilot`) - AI pair programming assistant
- **GitHub Copilot Chat** (`github.copilot-chat`) - Chat interface for Copilot
- **Code Runner** (`formulahendry.code-runner`) - Run code snippets quickly
- **Python** (`ms-python.python`) - Python language support
- **Pylance** (`ms-python.vscode-pylance`) - Fast Python language server
- **Docker** (`ms-azuretools.vscode-docker`) - Docker container management
- **YAML** (`redhat.vscode-yaml`) - YAML language support

These extensions will be automatically recommended when you open this workspace.

## Sign-In Issues

### Problem: Authentication Page Locks Up / Freezes (127.0.0.1:63061)

**Symptoms:**
- VS Code opens browser to `http://127.0.0.1:63061/?redirect_uri=vscode://...`
- Page loads but freezes or becomes unresponsive
- Authentication never completes
- This is **NOT** an IP ban - it's a local authentication flow issue

**This is a known VS Code authentication bug. Here are solutions:**

#### Quick Fix #1: Use Device Code Flow (Recommended)

This bypasses the broken localhost authentication:

1. Close all browser windows
2. In VS Code, press `Ctrl+Shift+P`
3. Type: `GitHub Copilot: Sign in Using Device Code`
4. You'll get a code like: `XXXX-XXXX`
5. Click the link or go to: https://github.com/login/device
6. Enter the device code
7. Authorize VS Code
8. Return to VS Code - authentication should complete

#### Quick Fix #2: Clear Authentication Cache

```bash
# Stop VS Code completely
killall code

# Clear authentication cache
rm -rf ~/.config/Code/User/globalStorage/github.copilot
rm -rf ~/.config/Code/User/globalStorage/github.github-authentication

# Clear browser cache for localhost
rm -rf ~/.cache/google-chrome/Default/Cache/*
rm -rf ~/.mozilla/firefox/*/cache2/*

# Restart VS Code
code .
```

#### Quick Fix #3: Change Default Browser

The issue often occurs with specific browsers:

```bash
# Set a different default browser
# For Firefox:
xdg-settings set default-web-browser firefox.desktop

# For Chrome:
xdg-settings set default-web-browser google-chrome.desktop

# For Chromium:
xdg-settings set default-web-browser chromium.desktop

# Then try signing in again
```

#### Quick Fix #4: Disable Hardware Acceleration

For remote systems (like Jetson at 192.168.1.145):

1. Edit VS Code settings: `Ctrl+,`
2. Search for: `disable hardware acceleration`
3. Enable: `Window: Disable Hardware Acceleration`
4. Restart VS Code

Or add to settings.json:
```json
{
  "window.titleBarStyle": "custom",
  "window.enableMenuBarMnemonics": false,
  "disable-hardware-acceleration": true
}
```

#### Quick Fix #5: Manual Token Authentication (No Browser Required)

Completely bypass browser authentication:

1. Generate GitHub Personal Access Token:
   - Go to: https://github.com/settings/tokens/new
   - Name: "VS Code on 192.168.1.145"
   - Expiration: 90 days (or as needed)
   - Scopes: Select `repo`, `workflow`, `user`, `read:org`, `copilot`
   - Click **Generate token**
   - **COPY THE TOKEN** (you won't see it again)

2. Configure Git to use the token:
   ```bash
   cd /home/curtis/avatar-pipeline
   
   # Store credentials
   git config --global credential.helper store
   
   # Update remote URL with token
   git remote set-url origin https://YOUR_TOKEN@github.com/curtisgc1/avatar-pipeline.git
   
   # Test
   git fetch
   ```

3. For Copilot, use the token in VS Code:
   - Install Copilot manually if not installed
   - When prompted for sign-in, use the device code method instead

#### Quick Fix #6: Port Already in Use

Check if port 63061 is blocked:

```bash
# Check what's using the port
sudo lsof -i :63061
sudo netstat -tulpn | grep 63061

# Kill any process using it
sudo kill -9 $(sudo lsof -t -i:63061)

# Restart VS Code
code .
```

#### Quick Fix #7: Firewall/Network Configuration

For Jetson Orin at 192.168.1.145:

```bash
# Allow localhost connections
sudo ufw allow from 127.0.0.1

# Check if SELinux is blocking (if applicable)
sudo setenforce 0  # Temporary

# Test localhost connectivity
curl http://127.0.0.1:63061
```

### Problem: Cannot Sign In to VS Code (General)

If you're experiencing other sign-in issues, follow these steps:

#### 1. Sign In to GitHub Account

VS Code requires authentication with GitHub to use Copilot and other features:

1. Open VS Code
2. Click on the **Account** icon in the bottom-left corner (person icon)
3. Select **Sign in to Sync Settings** or **Sign in with GitHub**
4. Follow the browser prompts to authorize VS Code
5. Return to VS Code after authorization

#### 2. Enable GitHub Copilot

After signing in:

1. Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
2. Type `GitHub Copilot: Sign In`
3. Follow the prompts to authorize Copilot
4. Verify you have an active Copilot subscription at https://github.com/settings/copilot

#### 3. Network/Firewall Issues

If you're on a restricted network (like at IP 192.168.1.145):

**Check Network Connectivity:**
```bash
# Test GitHub connectivity
ping github.com

# Test HTTPS access
curl -I https://github.com

# Test Copilot API
curl -I https://api.github.com
```

**Configure Proxy (if needed):**
```bash
# In VS Code settings.json
{
  "http.proxy": "http://proxy-server:port",
  "http.proxyStrictSSL": false
}
```

#### 4. Token-Based Authentication

If browser-based sign-in doesn't work:

1. Generate a Personal Access Token (PAT):
   - Go to https://github.com/settings/tokens
   - Click **Generate new token (classic)**
   - Select scopes: `repo`, `user`, `workflow`
   - Copy the generated token

2. Use token in VS Code:
   - Press `Ctrl+Shift+P`
   - Type `Git: Clone`
   - Use format: `https://<TOKEN>@github.com/curtisgc1/avatar-pipeline.git`

#### 5. SSH Key Setup (Alternative)

If HTTPS authentication fails, use SSH:

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to agent
ssh-add ~/.ssh/id_ed25519

# Copy public key
cat ~/.ssh/id_ed25519.pub
# Add this to GitHub: https://github.com/settings/keys

# Test connection
ssh -T git@github.com

# Change remote to SSH
cd /home/curtis/avatar-pipeline
git remote set-url origin git@github.com:curtisgc1/avatar-pipeline.git
```

## Common Issues and Solutions

### Issue: Copilot Not Working After Sign-In

**Solution:**
1. Verify Copilot status: Click Copilot icon in status bar
2. Check subscription: https://github.com/settings/copilot
3. Reload window: `Ctrl+Shift+P` → `Developer: Reload Window`
4. Reinstall extension: Uninstall and reinstall GitHub Copilot

### Issue: "Authentication Failed" Error

**Solution:**
1. Sign out completely: Account icon → Sign Out
2. Clear VS Code credentials:
   ```bash
   # Linux
   rm -rf ~/.config/Code/User/globalStorage/github.copilot
   
   # macOS
   rm -rf ~/Library/Application\ Support/Code/User/globalStorage/github.copilot
   ```
3. Restart VS Code
4. Sign in again

### Issue: Extensions Not Loading

**Solution:**
```bash
# Linux: Increase file watcher limit
echo fs.inotify.max_user_watches=524288 | sudo tee -a /etc/sysctl.conf
sudo sysctl -p

# Verify VS Code has network access
code --verbose
```

### Issue: Remote Development on Jetson (192.168.1.145)

If you're developing remotely on the Jetson Orin at 192.168.1.145:

**Option 1: Remote-SSH Extension**
1. Install **Remote - SSH** extension
2. Press `Ctrl+Shift+P` → `Remote-SSH: Connect to Host`
3. Enter: `curtis@192.168.1.145`
4. Select Linux platform
5. Sign in to GitHub from the remote session

**Option 2: Port Forwarding**
```bash
# From local machine, forward VS Code server port
ssh -L 8080:localhost:8080 curtis@192.168.1.145

# Then access VS Code server in browser
# http://localhost:8080
```

**Option 3: Code Server (Browser-based VS Code)**
```bash
# Install code-server on Jetson
curl -fsSL https://code-server.dev/install.sh | sh

# Start code-server
code-server --bind-addr 0.0.0.0:8080 --auth password

# Access from browser at http://192.168.1.145:8080
```

## Project-Specific Setup

### Python Environment

This project uses Python 3 with various dependencies:

```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Configure Python interpreter in VS Code
# Press Ctrl+Shift+P → "Python: Select Interpreter"
# Choose /usr/bin/python3 or your virtual environment
```

### Docker Integration

The project uses Docker for services:

```bash
# Verify Docker extension is installed
code --list-extensions | grep docker

# VS Code will detect docker-compose.yml automatically
```

## Verification Steps

After setup, verify everything works:

1. **GitHub Sign-In:**
   - Check bottom-left corner shows your GitHub username
   - Account icon should show "Signed in"

2. **Copilot Status:**
   - Status bar should show Copilot icon
   - No errors when opening Python files
   - Suggestions appear as you type

3. **Git Integration:**
   ```bash
   # Verify git works
   git status
   git remote -v
   ```

4. **Extensions:**
   - Press `Ctrl+Shift+X` to open Extensions view
   - All recommended extensions should be installed
   - No error badges on extension icons

## Getting Help

If you continue to experience issues:

1. **Check VS Code Logs:**
   - Press `Ctrl+Shift+P` → `Developer: Show Logs`
   - Look for authentication errors

2. **GitHub Copilot Logs:**
   - Press `Ctrl+Shift+P` → `GitHub Copilot: View Logs`

3. **Network Diagnostics:**
   ```bash
   # Test GitHub API
   curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
   
   # Test DNS resolution
   nslookup github.com
   
   # Test firewall
   telnet github.com 443
   ```

4. **Contact Support:**
   - VS Code: https://github.com/microsoft/vscode/issues
   - GitHub Copilot: https://support.github.com/

## Quick Reference

### Useful Commands

```bash
# Open VS Code from terminal
code .

# Open specific file
code main_pipeline.py

# Install extension from command line
code --install-extension github.copilot

# Check VS Code version
code --version

# Reset VS Code settings
rm -rf ~/.config/Code/User/settings.json
```

### Keyboard Shortcuts

- **Command Palette:** `Ctrl+Shift+P` (or `Cmd+Shift+P`)
- **Quick Open:** `Ctrl+P` (or `Cmd+P`)
- **Integrated Terminal:** `` Ctrl+` ``
- **Git Panel:** `Ctrl+Shift+G`
- **Extensions:** `Ctrl+Shift+X`
- **Settings:** `Ctrl+,`

## Additional Resources

- [VS Code Documentation](https://code.visualstudio.com/docs)
- [GitHub Copilot Documentation](https://docs.github.com/copilot)
- [VS Code Remote Development](https://code.visualstudio.com/docs/remote/remote-overview)
- [Python in VS Code](https://code.visualstudio.com/docs/languages/python)
