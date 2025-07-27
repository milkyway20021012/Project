#!/usr/bin/env python3
"""
最簡單的測試應用程式
用於診斷 404 錯誤
"""

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def index():
    return jsonify({
        "message": "Hello from Vercel!",
        "status": "ok"
    })

@app.route("/test")
def test():
    return jsonify({
        "message": "Test endpoint working!",
        "status": "ok"
    })

@app.route("/health")
def health():
    return jsonify({
        "status": "healthy",
        "message": "Health check passed"
    })

if __name__ == "__main__":
    app.run(debug=False, port=8080) 