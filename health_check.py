#!/usr/bin/env python3
"""
Health check endpoint for Render deployment
"""
from flask import Flask, jsonify
import os
from datetime import datetime

app = Flask(__name__)

@app.get("/")
def root():
    return jsonify({
        "service": "BearTech Token Analysis Bot",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    })

@app.get("/health")
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "BearTech Bot",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("RENDER", "local")
    })

@app.get("/status")
def status():
    return jsonify({
        "service": "BearTech Token Analysis Bot",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": {
            "render": bool(os.getenv("RENDER")),
            "python_version": os.getenv("PYTHON_VERSION", "unknown"),
            "telegram_token_set": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
            "goplus_key_set": bool(os.getenv("GOPLUS_API_KEY"))
        }
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
