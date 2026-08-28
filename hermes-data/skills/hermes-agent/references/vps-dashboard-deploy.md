# Hermes Dashboard — VPS Deployment Notes

## Issue: "Frontend not built" After Successful npm run build

**Symptom:** Dashboard starts, but all routes return `{"error":"Frontend not built. Run: cd web && npm run build"}` even after running `npm run build` successfully.

**Root cause:** Two different `web_dist` locations exist:
- Git source build output: `/app/hermes_cli/web_dist/` (where `npm run build` puts files)
- Python package installed location: `/usr/local/lib/python3.12/site-packages/hermes_cli/web_dist/` (what Python imports at runtime)

These are NOT the same path. The npm build lands in the git source tree, but Python serves from site-packages.

**Fix:**
```bash
cp -r /app/hermes_cli/web_dist/* /usr/local/lib/python3.12/site-packages/hermes_cli/web_dist/
```

**Prevention:** If dashboard always shows "frontend not built" on a fresh VPS install, check both locations first.

---

## Issue: Port 9119 Appears Busy But --status Shows Nothing

**Symptom:** `hermes dashboard` says "address already in use" but `hermes dashboard --status` shows no processes.

**Root cause:** The status command checks process list, not socket state. Another process (including a previous hermes dashboard run in a different session) may be holding the port.

**Diagnosis:**
```python
# Find inode of port 9119 listener
with open('/proc/net/tcp') as f:
    for line in f:
        parts = line.split()
        if len(parts) >= 10 and int(parts[1].split(':')[1], 16) == 9119 and parts[3] == '0A':
            inode = parts[9]
            # find PID from inode
            import os
            for pid in os.listdir('/proc'):
                if not pid.isdigit(): continue
                try:
                    for fd in os.listdir(f'/proc/{pid}/fd'):
                        if os.readlink(f'/proc/{pid}/fd/{fd}') == f'socket:[{inode}]':
                            print(pid, open(f'/proc/{pid}/cmdline').read().replace('\x00',' '))
                except: pass
```

**Fix:** `kill <PID>` then restart dashboard.

---

## Issue: Cannot Reach Dashboard from Public IP (but localhost works)

**Symptom:** `curl http://127.0.0.1:9119/` works. `curl http://<public-ip>:9119/` times out.

**Root cause:** Cloud provider's network-level firewall (Hetzner Cloud Firewall, AWS Security Groups, etc.) is blocking inbound traffic on that port. The service IS running correctly.

**Fix:** Open port 9119 TCP in the cloud console's firewall settings for your source IP (or 0.0.0.0/0 for unrestricted).

**Note on 0.0.0.0 bind:** On a single-interface VPS, binding to `0.0.0.0` is functionally identical to binding to the public IP. The security boundary is the cloud firewall, not the bind address. `--insecure` is required for non-loopback binds (it opts out of the dashboard's own security check), but the actual network exposure is controlled by the cloud provider's firewall.

---

## Quick Deploy Checklist (VPS)

1. `pip install 'hermes-agent[web,pty]'`
2. Build frontend: `cd /path/to/source/web && npm install && npm run build`
3. Copy to package: `cp -r /path/to/source/hermes_cli/web_dist/* /usr/local/lib/python3.12/site-packages/hermes_cli/web_dist/`
4. Open cloud firewall: port 9119 TCP from your IP
5. Start: `hermes dashboard --host 0.0.0.0 --port 9119 --insecure`
6. Test: `curl http://127.0.0.1:9119/` → should return HTML, not JSON error