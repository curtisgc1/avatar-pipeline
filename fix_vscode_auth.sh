#!/bin/bash
# VS Code Authentication Fix Script
# This script helps resolve VS Code sign-in issues, especially the 127.0.0.1:63061 lockup

set -e

echo "🔧 VS Code Authentication Fix Script"
echo "===================================="
echo ""

# Function to display menu
show_menu() {
    echo "Select a fix to try:"
    echo ""
    echo "1) Clear VS Code authentication cache (Quick Fix)"
    echo "2) Clear browser cache"
    echo "3) Kill process on port 63061"
    echo "4) Check and configure firewall"
    echo "5) Set Firefox as default browser"
    echo "6) Set Chrome as default browser"
    echo "7) Generate GitHub token instructions"
    echo "8) Show device code authentication instructions"
    echo "9) Run all automatic fixes"
    echo "0) Exit"
    echo ""
}

# Clear VS Code auth cache
clear_vscode_cache() {
    echo "🗑️  Clearing VS Code authentication cache..."
    
    # Kill VS Code processes
    killall code 2>/dev/null || echo "VS Code not running"
    
    # Clear GitHub authentication storage
    rm -rf ~/.config/Code/User/globalStorage/github.copilot 2>/dev/null && echo "  ✓ Cleared Copilot cache"
    rm -rf ~/.config/Code/User/globalStorage/github.github-authentication 2>/dev/null && echo "  ✓ Cleared GitHub auth cache"
    rm -rf ~/.vscode/extensions/github.copilot-* 2>/dev/null && echo "  ✓ Cleared Copilot extensions cache"
    
    echo "✅ Cache cleared! Please restart VS Code and try signing in again."
}

# Clear browser cache
clear_browser_cache() {
    echo "🗑️  Clearing browser cache for localhost..."
    
    # Chrome/Chromium
    rm -rf ~/.cache/google-chrome/Default/Cache/* 2>/dev/null && echo "  ✓ Cleared Chrome cache"
    rm -rf ~/.cache/chromium/Default/Cache/* 2>/dev/null && echo "  ✓ Cleared Chromium cache"
    
    # Firefox
    find ~/.mozilla/firefox/*/cache2 -type f -delete 2>/dev/null && echo "  ✓ Cleared Firefox cache"
    
    echo "✅ Browser cache cleared!"
}

# Kill process on port 63061
kill_port_process() {
    echo "🔪 Checking for processes on port 63061..."
    
    if lsof -i :63061 >/dev/null 2>&1; then
        echo "  Found process using port 63061"
        sudo lsof -i :63061
        echo ""
        read -p "Kill this process? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo kill -9 $(sudo lsof -t -i:63061) 2>/dev/null && echo "  ✓ Process killed"
        fi
    else
        echo "  ℹ️  No process using port 63061"
    fi
}

# Configure firewall
configure_firewall() {
    echo "🔥 Configuring firewall for localhost..."
    
    if command -v ufw >/dev/null 2>&1; then
        sudo ufw allow from 127.0.0.1 2>/dev/null && echo "  ✓ UFW configured for localhost"
    fi
    
    # Test localhost connectivity
    if curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:63061 2>/dev/null; then
        echo "  ✓ Localhost connectivity OK"
    else
        echo "  ℹ️  Port 63061 not responding (this is normal if VS Code isn't running)"
    fi
    
    echo "✅ Firewall configured!"
}

# Set Firefox as default
set_firefox_default() {
    echo "🦊 Setting Firefox as default browser..."
    
    if command -v firefox >/dev/null 2>&1; then
        xdg-settings set default-web-browser firefox.desktop 2>/dev/null && echo "  ✓ Firefox set as default"
    else
        echo "  ❌ Firefox not installed"
    fi
}

# Set Chrome as default
set_chrome_default() {
    echo "🌐 Setting Chrome/Chromium as default browser..."
    
    if command -v google-chrome >/dev/null 2>&1; then
        xdg-settings set default-web-browser google-chrome.desktop 2>/dev/null && echo "  ✓ Chrome set as default"
    elif command -v chromium >/dev/null 2>&1; then
        xdg-settings set default-web-browser chromium.desktop 2>/dev/null && echo "  ✓ Chromium set as default"
    else
        echo "  ❌ Chrome/Chromium not installed"
    fi
}

# Show token instructions
show_token_instructions() {
    echo "🔑 GitHub Personal Access Token Instructions"
    echo "==========================================="
    echo ""
    echo "1. Open your browser and go to:"
    echo "   https://github.com/settings/tokens/new"
    echo ""
    echo "2. Fill in the form:"
    echo "   - Note: 'VS Code on Jetson 192.168.1.145'"
    echo "   - Expiration: 90 days (or as needed)"
    echo "   - Scopes: Check these boxes:"
    echo "     ☑ repo (Full control of private repositories)"
    echo "     ☑ workflow (Update GitHub Action workflows)"
    echo "     ☑ user (Update user data)"
    echo "     ☑ read:org (Read org and team membership)"
    echo "     ☑ copilot (GitHub Copilot access)"
    echo ""
    echo "3. Click 'Generate token' and COPY the token"
    echo ""
    echo "4. Configure Git with the token:"
    echo "   cd /home/curtis/avatar-pipeline"
    echo "   git config --global credential.helper store"
    echo "   git remote set-url origin https://YOUR_TOKEN@github.com/curtisgc1/avatar-pipeline.git"
    echo "   git fetch"
    echo ""
    echo "5. For Copilot: Use device code authentication (option 8)"
    echo ""
}

# Show device code instructions
show_device_code_instructions() {
    echo "📱 Device Code Authentication Instructions"
    echo "=========================================="
    echo ""
    echo "This is the BEST way to sign in when the browser freezes!"
    echo ""
    echo "1. In VS Code, press: Ctrl+Shift+P"
    echo ""
    echo "2. Type and select:"
    echo "   'GitHub Copilot: Sign in Using Device Code'"
    echo ""
    echo "3. VS Code will show you a code like: XXXX-XXXX"
    echo ""
    echo "4. Either:"
    echo "   - Click the link VS Code provides, OR"
    echo "   - Manually go to: https://github.com/login/device"
    echo ""
    echo "5. Enter the device code"
    echo ""
    echo "6. Click 'Authorize' to grant VS Code access"
    echo ""
    echo "7. Return to VS Code - you should now be signed in!"
    echo ""
    echo "Note: This bypasses the broken localhost:63061 authentication"
    echo ""
}

# Run all fixes
run_all_fixes() {
    echo "🔧 Running all automatic fixes..."
    echo ""
    
    clear_vscode_cache
    echo ""
    clear_browser_cache
    echo ""
    kill_port_process
    echo ""
    configure_firewall
    echo ""
    
    echo "✅ All automatic fixes completed!"
    echo ""
    echo "Next steps:"
    echo "1. Restart VS Code: code ."
    echo "2. Try device code authentication (option 8)"
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Enter choice [0-9]: " choice
    echo ""
    
    case $choice in
        1) clear_vscode_cache ;;
        2) clear_browser_cache ;;
        3) kill_port_process ;;
        4) configure_firewall ;;
        5) set_firefox_default ;;
        6) set_chrome_default ;;
        7) show_token_instructions ;;
        8) show_device_code_instructions ;;
        9) run_all_fixes ;;
        0) echo "Goodbye!"; exit 0 ;;
        *) echo "❌ Invalid option. Please try again." ;;
    esac
    
    echo ""
    read -p "Press Enter to continue..."
    clear
done
