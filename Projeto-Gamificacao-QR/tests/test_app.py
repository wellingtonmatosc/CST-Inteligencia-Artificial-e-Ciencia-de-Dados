from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)


def test_health():
    response=client.get('/health')
    assert response.status_code==200
    assert response.json()['status']=='ok'


def test_public_pages_load():
    for path in ('/','/ranking','/admin','/q/TESTE'):
        response=client.get(path)
        assert response.status_code==200
        assert 'text/html' in response.headers.get('content-type','')
