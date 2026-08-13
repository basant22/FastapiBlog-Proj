from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app instance

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    # Checks if the server responds (adjust expected status code as needed)
    assert response.status_code in [200,302, 404]