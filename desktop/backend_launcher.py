import os

import uvicorn

from app.main import app


if __name__ == "__main__":
    host = os.getenv("NAVAGATOR_BACKEND_HOST", "127.0.0.1")
    port = int(os.getenv("NAVAGATOR_BACKEND_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
