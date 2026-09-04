"""Entry point for the FastAPI server.

    python src/main.py
    # or
    uvicorn api.app:app --app-dir src --reload
"""
import uvicorn

import config

if __name__ == "__main__":
    uvicorn.run(
        "api.app:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=False,
    )
