from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return {
        "status": "success",
        "message": "Vercel deployment test successful",
        "version": "1.0.0"
    }

@app.route('/health')
def health():
    return {
        "status": "healthy",
        "service": "LINE Bot API"
    }

if __name__ == "__main__":
    app.run(debug=True)
