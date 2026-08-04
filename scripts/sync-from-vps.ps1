# sync-from-vps.ps1 - pull VPS-truth files into the local hermes-data/ mirror.
#
# The VPS (/opt/hermes/hermes-data/) is the source of truth for these files;
# the local checkout is a one-way mirror. Run this BEFORE reading/writing any
# mirrored file (per AGENTS.md Local-VPS Sync Policy).
#
# Mirrors:
#   SOUL.md                                   -> hermes-data/SOUL.md
#   skills/<custom skills>                    -> hermes-data/skills/
#        domain/real-estate-area-research
#        domain/real-estate-portal-research
#        productivity/property-pricing-sources
#        productivity/property-rd
#        research/property-legal-analysis
#
# Behavior: SHA-256 compare first; auto-backup of any local file that differs
# (<file>.bak.<timestamp>); preflight check on SSH key + VPS reachability.
# To push local changes to the VPS, do it explicitly via scp - never silently.

$ErrorActionPreference = "Stop"

$VPS_HOST = "root@178.105.35.94"
$VPS_SKILLS_ROOT = "/opt/hermes/hermes-data/skills"
$LOCAL_MIRROR = Join-Path $PSScriptRoot "..\hermes-data"

$CUSTOM_SKILLS = @(
    "domain/real-estate-area-research",
    "domain/real-estate-portal-research",
    "productivity/property-pricing-sources",
    "productivity/property-rd",
    "research/property-legal-analysis"
)

function Preflight {
    $idrsa = Join-Path $env:USERPROFILE ".ssh\id_rsa"
    $ided = Join-Path $env:USERPROFILE ".ssh\id_ed25519"
    if ((-not (Test-Path $idrsa)) -and (-not (Test-Path $ided))) {
        Write-Host "WARN: no default SSH key found - non-default keys need ~/.ssh/config" -ForegroundColor Yellow
    }
    $ok = ssh -o ConnectTimeout=10 -o BatchMode=yes $VPS_HOST "echo ok" 2>$null
    if ($ok -ne "ok") {
        Write-Host "FATAL: VPS unreachable ($VPS_HOST). Aborting." -ForegroundColor Red
        exit 1
    }
    Write-Host "VPS reachable: $VPS_HOST" -ForegroundColor Green
}

function Sync-DirTree([string]$remoteDir, [string]$localDir) {
    $parent = Split-Path $localDir -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $remoteAbs = "${VPS_HOST}:${VPS_SKILLS_ROOT}/${remoteDir}"
    scp -o BatchMode=yes -q -r $remoteAbs $parent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  FAILED: scp $remoteAbs" -ForegroundColor Red
        exit 1
    }
    Write-Host "  pulled tree: $remoteDir -> $localDir" -ForegroundColor Green
}

function Sync-File([string]$remote, [string]$local) {
    $dir = Split-Path $local -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
    $remoteHash = (ssh -o BatchMode=yes $VPS_HOST "sha256sum $remote" 2>$null) -split "\s+" | Select-Object -First 1
    if (-not $remoteHash) {
        Write-Host "  skip (remote missing): $remote" -ForegroundColor DarkGray
        return
    }
    if (Test-Path $local) {
        $localHash = (Get-FileHash $local -Algorithm SHA256).Hash.ToLower()
        if ($localHash -eq $remoteHash) {
            Write-Host "  unchanged: $local" -ForegroundColor DarkGray
            return
        }
        $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
        $bak = "$local.bak.$stamp"
        Copy-Item $local $bak
        Write-Host "  backed up diff -> $bak" -ForegroundColor Yellow
    }
    scp -o BatchMode=yes -q "${VPS_HOST}:$remote" $local
    Write-Host "  pulled: $remote" -ForegroundColor Green
}

Preflight

Sync-File "/opt/hermes/hermes-data/SOUL.md" (Join-Path $LOCAL_MIRROR "SOUL.md")

foreach ($skill in $CUSTOM_SKILLS) {
    $local = Join-Path $LOCAL_MIRROR ("skills\" + ($skill -replace "/", "\"))
    Sync-DirTree $skill $local
}

Write-Host "`nDone. VPS is the source of truth; push changes back explicitly via scp." -ForegroundColor Cyan
