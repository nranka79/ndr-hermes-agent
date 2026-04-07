# ✅ Deployment Checklist

## Pre-Deployment

- [ ] Docker Desktop installed on Windows
  - Test: Open PowerShell, run `docker --version`
  - Should show: `Docker version 27.x.x...`

- [ ] Docker Hub account ready
  - Username: `nranka79`
  - Password: available

- [ ] All required files in `C:\Users\ruhaan\AntiGravity\`:
  - [ ] `Dockerfile` (✅ created)
  - [ ] `setup_oauth_credentials.py` (✅ you have)
  - [ ] `hermes_google_workspace.py` (✅ you have)
  - [ ] `requirements.txt` (should already exist)
  - [ ] `pyproject.toml` (should already exist)
  - [ ] `uv.lock` (should already exist)

## Build Phase

- [ ] Open PowerShell
- [ ] Navigate: `cd C:\Users\ruhaan\AntiGravity`
- [ ] Build image:
  ```powershell
  docker build -t nranka79/hermes-telegram:latest .
  ```
- [ ] Wait for completion (5-10 minutes)
- [ ] Verify build: `docker images | findstr hermes`
  - Should see: `nranka79/hermes-telegram   latest ...`

## Push Phase

- [ ] Login to Docker Hub:
  ```powershell
  docker login
  ```
  - Enter username: `nranka79`
  - Enter password: (your Docker Hub password)

- [ ] Push image:
  ```powershell
  docker push nranka79/hermes-telegram:latest
  ```
- [ ] Wait for completion (2-5 minutes)
- [ ] Verify on Docker Hub: https://hub.docker.com/r/nranka79/hermes-telegram
  - Should see `latest` tag in tags list

## Railway Configuration

- [ ] Go to Railway Dashboard
- [ ] Click on **hermes-telegram** project
- [ ] Go to **Settings**
- [ ] **Remove** any GitHub source:
  - If there's a GitHub section, remove it

- [ ] **Add Docker Image**:
  - Registry: `docker.io`
  - Image: `nranka79/hermes-telegram`
  - Tag: `latest`
  - Click Save

- [ ] Go to **Settings** → **Build Command**
  - Replace with:
    ```bash
    pip install -e '.[messaging]' requests
    ```
  - Save

- [ ] Go to **Settings** → **Start Command**
  - Replace with:
    ```bash
    python3 setup_oauth_credentials.py && exec hermes gateway
    ```
  - Save

## Deployment

- [ ] Click **Deploy** button in Railway
- [ ] Wait for build to complete (should be quick since image already exists)
- [ ] Check deployment logs for errors
- [ ] Expected output:
  ```
  ✓ Created setup_oauth_credentials.py
  ✓ Created hermes_google_workspace.py
  HERMES OAUTH CREDENTIALS SETUP
  ✓ Successfully created credentials for 3 account(s)
  ```

## Verification

- [ ] Check Railway **Logs** tab
  - Should see: `Hermes gateway started`

- [ ] Test in Telegram (@NDRHermes_bot):
  ```
  List my files from ndr@draas.com
  ```
  - Should return: Drive files

  ```
  List my emails from nishantranka@gmail.com
  ```
  - Should return: Gmail messages

  ```
  List my files from ndr@ahfl.in
  ```
  - Should return: AHFL Drive files

## Troubleshooting

**Docker build fails:**
- [ ] Verify you're in the AntiGravity directory
- [ ] Check that all files exist (especially requirements.txt)
- [ ] Check disk space (Docker needs ~5GB temp space)
- [ ] Try: `docker system prune` to clean up old images

**Docker push fails:**
- [ ] Verify you're logged in: `docker logout` then `docker login` again
- [ ] Check internet connection
- [ ] Verify username in image name is correct: `nranka79`

**Railway deployment fails:**
- [ ] Check that Docker image tag is exactly: `nranka79/hermes-telegram:latest`
- [ ] Check that image exists on Docker Hub
- [ ] Verify OAuth environment variables are still set in Railway
- [ ] Check Railway build/start logs for specific errors

**Telegram bot not responding:**
- [ ] Check Railway logs
- [ ] Verify Telegram bot token is still valid
- [ ] Check that credentials were created successfully
- [ ] Verify OAuth tokens in Railway environment variables are valid

---

## Success Criteria

✅ Docker image built locally
✅ Image pushed to Docker Hub
✅ Railway using Docker image (not GitHub)
✅ Build/start commands simplified
✅ Deployment successful
✅ Telegram bot responds with multi-account access

---

## Time Estimate

- Build: 5-10 minutes
- Push: 2-5 minutes
- Railway Config: 2 minutes
- Deploy: 3-5 minutes
- **Total: 15-25 minutes**

---

## Support

Need help? Check:
1. `BUILD_AND_PUSH_DOCKER.md` — Detailed build instructions
2. `DOCKER_QUICK_START.md` — Quick reference
3. Railway Dashboard → Logs → Check error messages
4. Docker Desktop → Check system resources
