from fastapi.testclient import TestClient

from app.main import ADMIN_UI_VERSION, app

client = TestClient(app)


def test_admin_page_versions_all_admin_assets_and_disables_cache():
    response = client.get('/admin')
    assert response.status_code == 200
    assert response.headers['cache-control'].startswith('no-store')
    assert f'data-admin-ui-version="{ADMIN_UI_VERSION}"' in response.text
    assert f'/static/js/admin.js?v={ADMIN_UI_VERSION}' in response.text
    assert f'/static/js/admin-analytics.js?v={ADMIN_UI_VERSION}' in response.text
    assert f'/static/css/admin-ops.css?v={ADMIN_UI_VERSION}' in response.text
    assert "if(e.persisted){location.reload();}" in response.text


def test_admin_static_assets_are_not_cached_during_homologation():
    response = client.get('/static/js/admin.js')
    assert response.status_code == 200
    assert response.headers['cache-control'].startswith('no-store')
