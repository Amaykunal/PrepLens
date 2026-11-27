import os, secrets
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
from fastapi.testclient import TestClient
from app.main import app


def test_auth_search_bookmark_compare():
    with TestClient(app) as c:
        assert c.get("/api/articles").status_code == 401
        email = f"{secrets.token_hex(4)}@example.com"
        assert c.post("/api/auth/register", json={"email": email, "password": "short"}).status_code == 422
        r = c.post("/api/auth/register", json={"email": email, "password": "password123"})
        assert r.status_code == 201
        h = {"Authorization": f"Bearer {r.json()['token']}"}
        assert c.post("/api/auth/login", json={"email": email, "password": "wrong-pass1"}).status_code == 401
        res = c.get("/api/articles", params={"q": "quad"}, headers=h).json()
        assert res["total"] == 1 and res["items"][0]["is_demo"]
        aid = res["items"][0]["id"]
        assert c.put(f"/api/bookmarks/{aid}", headers=h).status_code == 204
        assert len(c.get("/api/bookmarks", headers=h).json()) == 1
        cmp = c.get("/api/compare", params={"topic": "India-China Relations"}, headers=h).json()
        assert cmp["mode"] == "demo" and "LAC" in cmp["common"]
        assert c.get("/api/compare", params={"topic": "Nope"}, headers=h).status_code == 422
        assert c.get("/api/admin/stats", headers=h).status_code == 403
