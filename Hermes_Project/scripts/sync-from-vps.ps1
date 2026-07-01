<#
.SYNOPSIS
    Pulls VPS-sourced files from the Hetzner production box to this local checkout.
.DESCRIPTION
    The local hermes-data/ directory mirrors files from /opt/hermes/hermes-data/ on
    the Hetzner VPS. The VPS is the source of truth. Run this script BEFORE reading
    or editing any mirrored file (users.json, SOUL.md, etc.) to make sure you have
    the latest version.

    One-way pull only (VPS -> local). To push local changes to the VPS, do it
    explicitly via ssh + scp -- never silently.

    Backups: any local file that differs from the VPS is backed up to
    <file>.bak.<timestamp> before being overwritten.
.EXAMPLE
    pwsh scripts/sync-from-vps.ps1
.NOTES
    See hermes-data/connections/hetzner.md for the sync policy and full file list.
#>

$ErrorActionPreference = "Stop"

# ---- Config ----
$sshKey     = "$env:USERPROFILE\.ssh\hetzner_new"
$vpsHost    = "root@178.105.35.94"
$remoteBase = "/opt/hermes/hermes-data"
$localBase  = Join-Path $PSScriptRoot "..\hermes-data"

# Files to pull (one-way: VPS -> local). Extend as the mirror grows.
$files = @(
    "users.json",
    "SOUL.md"
)

# ---- Preflight ----
if (-not (Test-Path $sshKey)) {
    Write-Error "SSH key not found: $sshKey  (see hermes-data/connections/hetzner.md)"
    exit 1
}

try {
    ssh -i $sshKey -o BatchMode=yes -o ConnectTimeout=10 $vpsHost "echo ok" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "ssh preflight exited $LASTEXITCODE" }
} catch {
    Write-Error "Cannot reach $vpsHost. Check your network and the SSH key."
    exit 1
}

# ---- Sync loop ----
foreach ($f in $files) {
    $local  = Join-Path $localBase $f
    $remote = "${vpsHost}:${remoteBase}/${f}"

    # Ensure local parent dir exists
    $localDir = Split-Path $local -Parent
    if (-not (Test-Path $localDir)) {
        New-Item -ItemType Directory -Path $localDir -Force | Out-Null
    }

    # Remote hash (always, for comparison)
    $remoteHashRaw = ssh -i $sshKey -o BatchMode=yes $vpsHost "sha256sum '$remoteBase/$f'" 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "[skip]  $f - cannot read remote (missing or perms)"
        continue
    }
    $remoteHash = ($remoteHashRaw -split '\s+')[0]

    if (Test-Path $local) {
        $localHash = (Get-FileHash $local -Algorithm SHA256).Hash
        if ($remoteHash -eq $localHash) {
            Write-Host "[ok]    $f - already in sync"
            continue
        }
        $backup = "$local.bak.$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Copy-Item $local $backup
        Write-Host "[bkup]  $f -> $(Split-Path $backup -Leaf)"
    } else {
        Write-Host "[new]   $f (no local copy yet)"
    }

    scp -i $sshKey $remote $local
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[pull]  $f"
    } else {
        Write-Error "[FAIL]  $f - scp exited $LASTEXITCODE"
    }
}

Write-Host ""
Write-Host "Done. Source of truth: ${vpsHost}:${remoteBase}"
