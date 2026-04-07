# Docker Image Deployment Plan

## Overview
Build a Docker image locally with all files included, push to Docker Hub, and tell Railway to use it.

## Files Needed
- `setup_oauth_credentials.py` ✓ (already have)
- `hermes_google_workspace.py` ✓ (already have)
- `Dockerfile` (will create)

## Step-by-Step Plan

### Phase 1: Create Dockerfile
Create a simple Dockerfile that:
1. Extends from Railway's Python base image
2. Copies the two Python files
3. Installs dependencies
4. Sets up entry point

### Phase 2: Build Docker Image Locally
```bash
cd /c/Users/ruhaan/AntiGravity
docker build -t nranka79/hermes-telegram:latest .
```

### Phase 3: Push to Docker Hub
```bash
docker login  # (use your Docker Hub credentials)
docker push nranka79/hermes-telegram:latest
```

### Phase 4: Configure Railway to Use Docker Image
Go to Railway Dashboard:
- hermes-telegram project → Settings
- Change from "GitHub" to "Docker Image"
- Set registry image: `nranka79/hermes-telegram:latest`

### Phase 5: Simplify Build/Start Commands
**Build Command:**
```bash
pip install -e '.[messaging]' requests
```

**Start Command:**
```bash
python3 setup_oauth_credentials.py && exec hermes gateway
```

(Files are already in the image, so no need for complex setup)

### Phase 6: Deploy
Click Deploy in Railway dashboard

---

## Why This Works

✅ No GitHub (files are in the image)
✅ Simple build/start commands (files already present)
✅ Reproducible (everyone uses the same image)
✅ Fast (files don't need to be created at build time)
✅ Clean (no environment variable encoding issues)

---

## Prerequisites

You'll need:
- Docker installed locally
- Docker Hub account (free)
- Docker Hub username: `nranka79` (used in image name)

---

## Next Steps

1. Verify Docker is installed: `docker --version`
2. Create Dockerfile
3. Build locally
4. Push to Docker Hub
5. Update Railway settings
6. Deploy

