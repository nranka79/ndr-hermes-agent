# Flameback folder + binary upload (Oct 2026)

## Flameback filing location
- All Flameback Capital docs live in the `Flame Back` folder at root of ndr@draas.com Drive (id 1BN3SYoRutFCqiZbSoE8y876RbIuThGrw).
- Contains SHA / share-transfer / resignation / financials and (since Oct 2026) presentation decks. NO presentations subfolder — flat.
- When NDR says "file these in the Flameback folder": upload there directly with dated names, e.g. `Flameback JITO PMS Deck (Oct 2026).pdf`, `Flameback Multi-Strategy Portfolio (Oct 2026).pdf`.
- Files come from chat attachments at /mnt/uploads/<file_id>_<original_name> (read-only mount).

## Binary upload pattern (PDF/PPTX/docx — no native gws_drive tool)
The native gws_drive_* tools are text-only (create_file/update take text content).
For binary files use the GWS service directly:

```python
import os, sys
sys.path.insert(0, '/opt/hermes')
os.environ.pop('PYTHONPATH', None)          # PYTHONPATH shadows venv pkgs
from tools.gws_auth import build_service

svc = build_service('drive', 'v3', service_name='google-draas')
r = svc.files().create(
    body={'name': name, 'parents': [folder_id], 'mimeType': 'application/pdf'},
    media_body=local_path, fields='id,name,size,webViewLink').execute()
```

Run via `env -u PYTHONPATH /opt/hermes/.venv/bin/python3 /tmp/script.py`, then VERIFY by listing the folder with gws_drive_list (GWS writes can be ghosts — read-back rule).