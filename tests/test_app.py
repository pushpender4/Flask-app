from app import app

def test_homepage():
    client = app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert b"Hello from Flask CI/CD, rolllng image policy new" in response.data
