import pytest
from app import create_app

@pytest.fixture
def client():
    app = create_app(testing=True)
    with app.test_client() as c:
        yield c

def test_homepage_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200
