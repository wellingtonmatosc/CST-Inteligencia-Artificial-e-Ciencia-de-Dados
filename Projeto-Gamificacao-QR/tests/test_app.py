from pathlib import Path

from fastapi.testclient import TestClient
from app.main import app

client=TestClient(app)
ROOT=Path(__file__).resolve().parents[1]


def test_health():
    response=client.get('/health')
    assert response.status_code==200
    assert response.json()['status']=='ok'


def test_public_pages_load():
    for path in ('/','/ranking','/admin','/q/TESTE'):
        response=client.get(path)
        assert response.status_code==200
        assert 'text/html' in response.headers.get('content-type','')


def test_admin_assets_are_versioned():
    response=client.get('/admin')
    html=response.text
    assert 'data-admin-ui-version=' in html
    assert '/static/js/common.js?v=' in html
    assert '/static/js/admin.js?v=' in html
    assert '/static/js/admin-analytics.js?v=' in html


def test_common_js_does_not_autoload_legacy_admin_scripts():
    common=(ROOT/'app'/'static'/'js'/'common.js').read_text(encoding='utf-8')
    assert 'admin-event-control.js' not in common
    assert 'admin-monitoring.js' not in common
    assert 'admin-ranking-rules.js' not in common
