# Build and Push Docker Image

## Prerequisites

1. **Docker Desktop installed** on Windows
   - Download from: https://www.docker.com/products/docker-desktop
   - Install and restart Windows
   - Verify: Open PowerShell and run `docker --version`

2. **Docker Hub account**
   - Already have: nranka79
   - Know your password

## Step 1: Verify Docker Works

Open PowerShell and run:
```powershell
docker --version
```

Should show something like: `Docker version 27.0.0, build...`

## Step 2: Build the Docker Image

In PowerShell, navigate to AntiGravity folder and build:

```powershell
cd C:\Users\ruhaan\AntiGravity
docker build -t nranka79/hermes-telegram:latest .
```

**This will:**
- Read the Dockerfile
- Install Python 3.13
- Copy your files
- Install dependencies
- Create the image (~5-10 minutes)

**Expected output:**
```
[+] Building 123.4s
...
=> => naming to docker.io/nranka79/hermes-telegram:latest
```

## Step 3: Verify the Build

```powershell
docker images
```

Should show `nranka79/hermes-telegram` in the list with tag `latest`

## Step 4: Test Run (Optional)

To verify everything works:

```powershell
docker run --rm nranka79/hermes-telegram:latest python3 -c "import setup_oauth_credentials; print('✓ Files found')"
```

## Step 5: Login to Docker Hub

```powershell
docker login
```

**When prompted:**
- Username: `nranka79`
- Password: (your Docker Hub password)

## Step 6: Push to Docker Hub

```powershell
docker push nranka79/hermes-telegram:latest
```

**This will:**
- Upload image to Docker Hub
- Takes 2-5 minutes depending on internet

**Expected output:**
```
The push refers to repository [docker.io/nranka79/hermes-telegram]
latest: digest: sha256:abc123... size: 1234567
```

## Step 7: Verify on Docker Hub

Go to: https://hub.docker.com/r/nranka79/hermes-telegram

Should see your image with tag `latest`

---

## Railway Configuration

Once push completes:

1. Go to Railway Dashboard → hermes-telegram project
2. Click Settings
3. **Remove Git Source** (if any)
4. **Add Docker Image**:
   - Registry: `docker.io`
   - Image: `nranka79/hermes-telegram`
   - Tag: `latest`
5. Save

## Update Build/Start Commands

### Build Command:
```bash
pip install -e '.[messaging]' requests
```

### Start Command:
```bash
python3 setup_oauth_credentials.py && exec hermes gateway
```

## Deploy

Click **Deploy** in Railway dashboard.

---

## Troubleshooting

**"docker: command not found"**
- Docker Desktop not installed
- Or not in PATH
- Restart PowerShell after installing Docker Desktop

**"Error response from daemon: Get "https://registry.docker.com/v2/": unauthorized"**
- Credentials incorrect
- Run: `docker logout` then `docker login` again

**Build fails: "requirements.txt not found"**
- Make sure you're in the AntiGravity directory
- `cd C:\Users\ruhaan\AntiGravity` first

**Push fails: "denied: requested access to the resource is denied"**
- Wrong username in image name
- Change `nranka79` in all commands to your Docker Hub username

---

## Files Reference

- `Dockerfile` — Build recipe
- `setup_oauth_credentials.py` — OAuth credential setup
- `hermes_google_workspace.py` — Google Workspace integration
- `requirements.txt`, `pyproject.toml`, `uv.lock` — Dependencies (copied automatically)

