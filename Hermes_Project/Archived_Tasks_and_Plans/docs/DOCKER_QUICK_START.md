# 🐳 Docker Image Deployment - Quick Start

## What We're Doing

1. **Build** a Docker image locally (includes all your files)
2. **Push** to Docker Hub (your private image registry)
3. **Deploy** from Railway using the Docker image (no GitHub needed)

## Files Ready

✅ `Dockerfile` — Build recipe (created)
✅ `setup_oauth_credentials.py` — Credential setup (you have)
✅ `hermes_google_workspace.py` — Google integration (you have)
✅ `BUILD_AND_PUSH_DOCKER.md` — Detailed instructions (created)

## Quick Commands (Windows PowerShell)

### 1. Build Image
```powershell
cd C:\Users\ruhaan\AntiGravity
docker build -t nranka79/hermes-telegram:latest .
```
⏱️ Takes ~5-10 minutes (first time installs Python, packages, etc.)

### 2. Login to Docker Hub
```powershell
docker login
```
Username: `nranka79`
Password: (your Docker Hub password)

### 3. Push Image
```powershell
docker push nranka79/hermes-telegram:latest
```
⏱️ Takes ~2-5 minutes (uploads to Docker Hub)

### 4. Configure Railway
Go to Railway Dashboard:
- **hermes-telegram** project → **Settings**
- Remove GitHub source (if present)
- Add **Docker Image**:
  - Registry: `docker.io`
  - Image: `nranka79/hermes-telegram`
  - Tag: `latest`

### 5. Update Commands in Railway

**Build Command:**
```bash
pip install -e '.[messaging]' requests
```

**Start Command:**
```bash
python3 setup_oauth_credentials.py && exec hermes gateway
```

### 6. Deploy
Click **Deploy** button in Railway

---

## Timeline

| Step | Time | What Happens |
|------|------|---|
| Build | 5-10 min | Creates image with all files |
| Login | 30 sec | Docker Hub authentication |
| Push | 2-5 min | Uploads image to Docker Hub |
| Railway Config | 2 min | Update deployment settings |
| Deploy | 3-5 min | Railway pulls image & starts |
| **Total** | **15-25 min** | ✅ Hermes running with multi-account support |

---

## Why This Works

✅ **No GitHub** — Files are in the Docker image
✅ **No Environment Variable Encoding** — Files are copied directly
✅ **Simple Commands** — Build/start just run normally
✅ **Reproducible** — Same image every time
✅ **Secure** — Private image, only you can push/pull

---

## Need Help?

- **Docker not found?** — Install Docker Desktop from https://docker.com
- **Build fails?** — See "Troubleshooting" in BUILD_AND_PUSH_DOCKER.md
- **Push fails?** — Verify username is correct: `nranka79`
- **Railway config?** — Settings → Docker Image (not GitHub)

---

## Next Steps

1. ✅ Install Docker Desktop (if needed)
2. ✅ Open PowerShell
3. ✅ Follow the 6 quick commands above
4. ✅ Check Railway dashboard
5. ✅ Test in Telegram bot

**Ready? Let me know when you've built the image and I'll help with Railway configuration!**
