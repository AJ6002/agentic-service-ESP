import os
import sys

# Ensure root project directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import uvicorn
from src.api.fastapi_app import app

if __name__ == "__main__":
    uvicorn.run("src.api.fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
