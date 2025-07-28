# Flask DevOps CI/CD Project

A simple Python Flask app with CI/CD using GitHub Actions and Docker.

## Run Locally
```bash
docker build -t flask-cicd-app .
docker run -p 5000:5000 flask-cicd-app
