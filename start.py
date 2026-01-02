#!/usr/bin/env python3
"""Entry point for RISE AI Trading Bot deployment."""

import os
import uvicorn
from app.api.server import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    host = "0.0.0.0"
    
    print(f"🚀 Starting RISE AI Trading Bot on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        access_log=True,
        log_level="info"
    )