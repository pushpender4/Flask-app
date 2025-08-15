from app.main import app  

def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Flask CI/CD Dashboard" in response.data