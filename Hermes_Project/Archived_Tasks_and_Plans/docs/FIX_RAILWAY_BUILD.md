# Fix Railway Build Error

The build is failing because environment variables are being treated as secrets but some are empty.

## Quick Troubleshooting

### Option 1: Verify Variables (Recommended First)

1. Go to Railway Dashboard
2. Click Hermes Service → Variables
3. Check ALL 6 variables are filled (no empty ones)
4. Look for typos in variable names
5. Scroll down to make sure all are visible

**If you find empty or incomplete variables:**
- Delete them
- Re-add them with the correct complete values
- Click Save

### Option 2: Simplify Build (If variables are correct)

If all variables look good but build still fails, we can update the build command to skip the environment variable loading at build time:

**Current build command:**
```
pip install -e '.[messaging]' requests && npm install -g @googleworkspace/cli
```

**This doesn't actually need the OAuth variables** - they're only used at runtime. So the error is likely due to:
- A variable with an empty name
- A variable with incomplete value
- Cached build state

### Option 3: Force Clean Rebuild

1. Go to Railway Dashboard
2. Find the service
3. Look for "Redeploy" or "Deploy" options
4. Try "Clean Redeploy" or "Force Deploy" if available

---

## What To Do Now

1. **Check all 6 variables are complete and saved** ← Do this first!
2. If all look good, try clicking Deploy again
3. If still fails, let me know and we'll update the build command

**Let me know which option you want to try!**
