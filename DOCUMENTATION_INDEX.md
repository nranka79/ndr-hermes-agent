# Hermes Multi-Account Documentation Index

Quick navigation guide for all documentation and implementation files.

---

## 📋 Quick Reference

### 🚀 Start Here (For Immediate Action)
- **[QUICK_START_MULTI_ACCOUNT.md](QUICK_START_MULTI_ACCOUNT.md)** (5 min read)
  - Quick reference card
  - Copy-paste commands
  - 20-minute total setup time
  - Perfect for "just tell me what to do"

### ✅ Implementation Status
- **[IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)** (10 min read)
  - What's been done ✅
  - What needs user action 🔄
  - Complete step-by-step phases
  - Testing instructions

---

## 📚 Detailed Guides

### 🔐 Setup Guides (Step-by-Step)
- **[MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md)** (20 min read)
  - **Account 1: nishantranka@gmail.com (OAuth 2.0)**
    - Create OAuth credentials
    - Generate refresh token
    - Store in Railway
  - **Account 2: ndr@ahfl.in (Service Account + DWD)**
    - Create service account
    - Enable domain-wide delegation
    - Add OAuth scopes
    - Store in Railway
  - **Account 3: ndr@draas.com (Reference)**
    - Already configured
    - For reference only
  - **Multi-Account Configuration**
    - Configuration structure (JSON)
    - google_account_switcher.py code
    - Usage examples
    - Testing & Troubleshooting

### 🏗️ Architecture & Usage
- **[MULTI_ACCOUNT_IMPLEMENTATION.md](MULTI_ACCOUNT_IMPLEMENTATION.md)** (30 min read)
  - **Overview** - What's been implemented
  - **Architecture** - System design diagram
  - **Files Created** - Description of each component
  - **Implementation Checklist** - What's done vs pending
  - **Usage in Hermes Skills** - How to use call_gws()
  - **Configuration Structure** - ACCOUNTS_CONFIG dictionary
  - **Troubleshooting** - Solutions for common errors
  - **Summary of Changes** - Features and status table
  - **Next Steps** - Chronological guide

### 🎛️ Google Workspace CLI Reference
- **[GWS_CLI_HERMES_GUIDE.md](GWS_CLI_HERMES_GUIDE.md)** (25 min read)
  - **Overview** - What is gws CLI
  - **Setup** - Environment variables
  - **Command Structure** - How gws commands work
  - **Example Commands** - All 18+ services documented
  - **Hermes Skill Example** - How to teach Hermes to use gws
  - **Testing Commands** - Try gws locally
  - **All Available Services** - Complete list
  - **Troubleshooting** - By error type
  - **Benefits Table** - gws vs Python wrapper
  - **Resources** - Links to official docs

### 🔗 Integrations Guide
- **[INTEGRATIONS_SETUP.md](INTEGRATIONS_SETUP.md)** (20 min read)
  - **GitHub Sync** - Automatic backup configuration
  - **Google Workspace** - Full setup guide
  - **Troubleshooting** - For both integrations
  - **Summary Table** - Components and status
  - **Next Steps** - Implementation sequence

### 🎤 Voice Settings
- **[VOICE_SETTINGS_UPDATE.md](VOICE_SETTINGS_UPDATE.md)** (5 min read)
  - Voice response behavior changed
  - Text by default, `/voice on` to enable
  - Already applied and working ✅

---

## 💻 Code Files

### Core Implementation
- **[google_account_switcher.py](google_account_switcher.py)** (128 lines)
  - Intelligent account routing
  - DWD + OAuth support
  - gws CLI wrapper function call_gws()
  - Automatically deployed to Railway at /data/hermes/
  - **Usage:**
    ```python
    from google_account_switcher import call_gws
    result = call_gws("ndr@ahfl.in", "drive", "files", "list", {"pageSize": 5})
    ```

### Deployment Tools
- **[deploy_multi_account.py](deploy_multi_account.py)** (197 lines)
  - Deploys google_account_switcher.py to Railway
  - Updates Railway service configuration
  - Creates setup instructions
  - **Usage:**
    ```bash
    export RAILWAY_TOKEN=<your_token>
    python deploy_multi_account.py
    ```

### Supporting Integrations
- **[github_sync_daemon.py](github_sync_daemon.py)**
  - Automatic backup to GitHub (every 5 min)
  - REST API-based (no git binary required)
  - Already deployed and working ✅

- **[hermes_google_workspace.py](hermes_google_workspace.py)**
  - Python wrapper for Google Workspace APIs
  - Available if needed for direct API access
  - Included as fallback option

- **[deploy_integrations.py](deploy_integrations.py)**
  - Original integration deployment script
  - Used to deploy github_sync_daemon.py and hermes_google_workspace.py

---

## 🗂️ How to Navigate

### "I just want to get it working fast" ⚡
1. Start: [QUICK_START_MULTI_ACCOUNT.md](QUICK_START_MULTI_ACCOUNT.md)
2. Follow: 4 phases (20 minutes)
3. Test: Send message to @NDRHermes_bot

### "I want to understand the full system" 🧠
1. Start: [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md)
2. Read: [MULTI_ACCOUNT_IMPLEMENTATION.md](MULTI_ACCOUNT_IMPLEMENTATION.md)
3. Reference: [GWS_CLI_HERMES_GUIDE.md](GWS_CLI_HERMES_GUIDE.md)
4. Deep dive: [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md)

### "I need to set up OAuth for nishantranka@gmail.com" 🔐
1. Go to: [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md) → **Account 1**
2. Follow: 3-step process with copy-paste code
3. Verify: Run Python script to get tokens

### "I need to set up service account for ndr@ahfl.in" 🛡️
1. Go to: [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md) → **Account 2**
2. Follow: 5-step process with screenshots
3. Configure: Domain-wide delegation in ahfl.in Admin

### "I want to add a 4th account" ➕
1. Read: [MULTI_ACCOUNT_IMPLEMENTATION.md](MULTI_ACCOUNT_IMPLEMENTATION.md) → **Configuration Structure**
2. Modify: ACCOUNTS_CONFIG dictionary in google_account_switcher.py
3. Redeploy: Use deploy_multi_account.py script

### "I'm getting errors" 🐛
1. Check: [MULTI_ACCOUNT_IMPLEMENTATION.md](MULTI_ACCOUNT_IMPLEMENTATION.md) → **Troubleshooting**
2. Reference: [GWS_CLI_HERMES_GUIDE.md](GWS_CLI_HERMES_GUIDE.md) → **Troubleshooting**
3. Check Railway logs: `railway logs | head -50`

---

## 📊 Status Overview

| Component | Status | File | Setup Required |
|-----------|--------|------|---|
| **gws CLI** | ✅ Installed | GWS_CLI_HERMES_GUIDE.md | None (auto-installed) |
| **Primary Account (draas)** | ✅ Configured | QUICK_START | None (ready to use) |
| **OAuth Account (personal)** | 🔄 Pending | MULTI_ACCOUNT_SETUP.md | 5 min OAuth flow |
| **DWD Account (ahfl.in)** | 🔄 Pending | MULTI_ACCOUNT_SETUP.md | 10 min service account |
| **Switcher Module** | ✅ Created | google_account_switcher.py | Auto-deployed |
| **GitHub Sync** | ✅ Deployed | github_sync_daemon.py | Add GITHUB_TOKEN |
| **Documentation** | ✅ Complete | DOCUMENTATION_INDEX.md | This file |

---

## 🎯 Recommended Reading Order

### For Immediate Setup (Total: 30 minutes)
1. This file (5 min) - You're reading it! ✓
2. [QUICK_START_MULTI_ACCOUNT.md](QUICK_START_MULTI_ACCOUNT.md) (5 min)
3. [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md) - Account 1 section (10 min)
4. [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md) - Account 2 section (10 min)

### For Full Understanding (Total: 60 minutes)
1. This file (5 min)
2. [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) (10 min)
3. [MULTI_ACCOUNT_IMPLEMENTATION.md](MULTI_ACCOUNT_IMPLEMENTATION.md) (20 min)
4. [GWS_CLI_HERMES_GUIDE.md](GWS_CLI_HERMES_GUIDE.md) (15 min)
5. [MULTI_ACCOUNT_SETUP.md](MULTI_ACCOUNT_SETUP.md) (10 min)

### For Reference Later
- Keep [QUICK_START_MULTI_ACCOUNT.md](QUICK_START_MULTI_ACCOUNT.md) handy
- Bookmark [GWS_CLI_HERMES_GUIDE.md](GWS_CLI_HERMES_GUIDE.md) for gws commands
- Reference [MULTI_ACCOUNT_IMPLEMENTATION.md](MULTI_ACCOUNT_IMPLEMENTATION.md) for usage examples

---

## 🔗 Direct Links to Specific Sections

### Common Tasks
- **Setup OAuth tokens** → [MULTI_ACCOUNT_SETUP.md#account-1](MULTI_ACCOUNT_SETUP.md)
- **Create service account** → [MULTI_ACCOUNT_SETUP.md#account-2](MULTI_ACCOUNT_SETUP.md)
- **Add Railway variables** → [IMPLEMENTATION_COMPLETE.md#phase-3](IMPLEMENTATION_COMPLETE.md)
- **Use in Hermes code** → [MULTI_ACCOUNT_IMPLEMENTATION.md#usage-in-hermes-skills](MULTI_ACCOUNT_IMPLEMENTATION.md)
- **Troubleshoot errors** → [MULTI_ACCOUNT_IMPLEMENTATION.md#troubleshooting](MULTI_ACCOUNT_IMPLEMENTATION.md)
- **List gws commands** → [GWS_CLI_HERMES_GUIDE.md#example-commands](GWS_CLI_HERMES_GUIDE.md)

### Configuration
- **ACCOUNTS_CONFIG structure** → [MULTI_ACCOUNT_IMPLEMENTATION.md#configuration-structure](MULTI_ACCOUNT_IMPLEMENTATION.md)
- **Railway env variables** → [QUICK_START_MULTI_ACCOUNT.md#3️⃣-add-to-railway](QUICK_START_MULTI_ACCOUNT.md)
- **gws environment setup** → [GWS_CLI_HERMES_GUIDE.md#setup](GWS_CLI_HERMES_GUIDE.md)

---

## 💡 Pro Tips

1. **Copy-paste from QUICK_START** - Most commands are ready to run
2. **Use railway CLI** - Faster than dashboard: `railway variable set NAME VALUE`
3. **Keep logs open** - Railway logs help debug: `railway logs --tail 50`
4. **Test one account at a time** - Add OAuth first, then service account
5. **gws --help** - Use in Railway terminal to see all commands

---

## 📞 Support

**Need help?**
1. Check the relevant guide above
2. Search "Troubleshooting" section in that guide
3. Review Railway logs: `railway logs | grep error`
4. Check environment variables are set: `railway variable list`

**Found an issue?**
1. Note the exact error message
2. Check [MULTI_ACCOUNT_IMPLEMENTATION.md#troubleshooting](MULTI_ACCOUNT_IMPLEMENTATION.md#troubleshooting)
3. Verify environment variables match exactly
4. Redeploy Railway and check logs

---

**Last Updated:** March 19, 2026
**Status:** Implementation Complete ✅ - Awaiting User Configuration 🔄

Good luck! 🚀
