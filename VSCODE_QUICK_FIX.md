# 🚨 QUICK FIX: VS Code Authentication Freezing at 127.0.0.1:63061

## Problem
VS Code opens browser to `http://127.0.0.1:63061/?redirect_uri=vscode://...` but the page freezes/locks up.

## ✅ BEST SOLUTION: Use Device Code Authentication

**This bypasses the broken localhost authentication completely!**

### Steps:

1. **Close any frozen browser windows**

2. **In VS Code, press:** `Ctrl+Shift+P`

3. **Type and select:** `GitHub Copilot: Sign in Using Device Code`

4. **VS Code will show a code** like: `ABCD-1234`

5. **Click the link** VS Code provides, or manually go to:
   ```
   https://github.com/login/device
   ```

6. **Enter the device code** from step 4

7. **Click "Authorize"** to grant VS Code access

8. **Return to VS Code** - you should now be signed in! ✅

---

## 🔧 Alternative: Run Automated Fix Script

```bash
cd /home/curtis/avatar-pipeline
./fix_vscode_auth.sh
```

Select option `8` for device code instructions or option `9` to run all fixes.

---

## 🛠️ Manual Cache Clear (If Device Code Doesn't Work)

```bash
# Stop VS Code
killall code

# Clear authentication cache
rm -rf ~/.config/Code/User/globalStorage/github.copilot
rm -rf ~/.config/Code/User/globalStorage/github.github-authentication

# Restart VS Code
code .
```

Then try device code authentication again.

---

## 📋 Full Documentation

For more solutions and troubleshooting, see:
- **[VSCODE_SETUP.md](VSCODE_SETUP.md)** - Complete VS Code setup guide
- **[README.md](README.md)** - Project documentation

---

## ❓ Why Does This Happen?

- The localhost:63061 authentication is a known VS Code bug
- It's **NOT** an IP ban - your IP 192.168.1.145 is fine
- The device code flow is more reliable for remote systems like Jetson Orin
- Some browsers don't handle the `vscode://` protocol redirect properly

---

## 💡 Pro Tip

Once signed in via device code, VS Code will remember your authentication and you won't need to repeat this process unless you sign out or clear cache.
