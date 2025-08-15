from flask import Flask

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Flask CI/CD, this is a healthy version 11"

@app.route('/health')
def health():
    return "OK", 200

# @app.route("/health")
# def health():
#     return "FAIL", 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
