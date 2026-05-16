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

import io

def test_parse_page_returns_200(client):
    response = client.get('/parse')
    assert response.status_code == 200

def test_import_page_returns_200(client):
    response = client.get('/import')
    assert response.status_code == 200

def test_upload_pdf_no_file_returns_400(client):
    response = client.post('/parse/upload', data={})
    assert response.status_code == 400

def test_upload_excel_no_file_returns_400(client):
    response = client.post('/import/upload', data={})
    assert response.status_code == 400

def test_questions_page_returns_200(client):
    response = client.get('/questions')
    assert response.status_code == 200

def test_export_page_returns_200(client):
    response = client.get('/export')
    assert response.status_code == 200

def test_api_questions_returns_json(client):
    response = client.get('/api/questions')
    assert response.status_code == 200
    assert response.is_json

def test_export_word_no_questions_returns_400(client):
    response = client.post('/export/download', json={'ids': [], 'format': 'word', 'show_answers': False})
    assert response.status_code == 400

def test_quiz_page_returns_200(client):
    response = client.get('/quiz')
    assert response.status_code == 200

def test_quiz_one_no_questions_redirects(client):
    response = client.get('/quiz/one')
    # Either redirects (empty DB) or shows first question (DB has data)
    assert response.status_code in (200, 302)

def test_quiz_all_returns_200(client):
    response = client.get('/quiz/all')
    assert response.status_code == 200

def test_quiz_result_no_result_redirects(client):
    response = client.get('/quiz/result')
    assert response.status_code in (200, 302)
