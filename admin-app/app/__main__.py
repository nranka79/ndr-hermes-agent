import os
import uvicorn

from . import create_app

app = create_app()

if __name__ == "__main__":
    host = os.environ.get("ADMIN_APP_HOST", "0.0.0.0")
    port = int(os.environ.get("ADMIN_APP_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
