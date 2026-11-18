import json
import subprocess
import zipfile
from pathlib import Path

import pytest

import app as server


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(server.time, "sleep", lambda _: None)
    return server.app.test_client()


def roll(monkeypatch, value):
    monkeypatch.setattr(server.random, "randint", lambda a, b: value if b == 4 else 0)


def test_returns_brackets_for_supported_year(client, monkeypatch):
    roll(monkeypatch, 2)
    resp = client.get("/tax-calculator/tax-year/2022")
    assert resp.status_code == 200
    assert resp.json["tax_brackets"][0] == {"min": 0, "max": 50197, "rate": 0.15}


def test_unsupported_year_is_404(client, monkeypatch):
    roll(monkeypatch, 2)
    resp = client.get("/tax-calculator/tax-year/1999")
    assert resp.status_code == 404
    assert resp.json["errors"][0]["code"] == "NOT_FOUND"


def test_non_numeric_year_is_404(client, monkeypatch):
    roll(monkeypatch, 2)
    assert client.get("/tax-calculator/tax-year/abc").status_code == 404


def test_random_failure_is_500(client, monkeypatch):
    roll(monkeypatch, 1)
    resp = client.get("/tax-calculator/tax-year/2022")
    assert resp.status_code == 500
    assert resp.json["errors"][0]["code"] == "INTERNAL_SERVER_ERROR"


def test_landing_and_deck_are_served(client):
    assert b"tax-calculator/tax-year" in client.get("/").data
    assert client.get("/deck").status_code == 200


@pytest.fixture(autouse=True)
def reset_rate_limit():
    server._calls.clear()


def test_rate_limited_returns_429_with_retry_after(client, monkeypatch):
    roll(monkeypatch, 2)
    url = "/tax-calculator/rate-limited/tax-year/2022"
    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 200
    resp = client.get(url)
    assert resp.status_code == 429
    assert resp.json["errors"][0]["code"] == "RATE_LIMITED"
    assert 1 <= int(resp.headers["Retry-After"]) <= 3


def test_rate_limit_resets_after_window(client, monkeypatch):
    roll(monkeypatch, 2)
    clock = [100.0]
    monkeypatch.setattr(server.time, "monotonic", lambda: clock[0])
    url = "/tax-calculator/rate-limited/tax-year/2022"
    client.get(url)
    client.get(url)
    assert client.get(url).status_code == 429
    clock[0] += server.RATE_LIMIT_WINDOW
    assert client.get(url).status_code == 200


def test_secure_requires_api_key(client, monkeypatch):
    roll(monkeypatch, 2)
    monkeypatch.setenv("TAX_API_KEY", "s3cret")
    url = "/tax-calculator/secure/tax-year/2022"
    assert client.get(url).status_code == 401
    assert client.get(url, headers={"X-API-Key": "wrong"}).status_code == 403
    assert client.get(url, headers={"X-API-Key": "clé"}).status_code == 403
    resp = client.get(url, headers={"X-API-Key": "s3cret"})
    assert resp.status_code == 200
    assert resp.json["tax_brackets"][0]["rate"] == 0.15


def test_secure_without_server_key_is_503(client, monkeypatch):
    monkeypatch.delenv("TAX_API_KEY", raising=False)
    assert client.get("/tax-calculator/secure/tax-year/2022").status_code == 503


def test_v2_returns_new_bracket_shape(client, monkeypatch):
    roll(monkeypatch, 2)
    resp = client.get("/tax-calculator/v2/tax-year/2022")
    assert resp.status_code == 200
    brackets = resp.json["brackets"]
    assert brackets[0] == {"lower": 0, "upper": 50197, "rate_percent": 15.0}
    assert brackets[1]["rate_percent"] == 20.5
    assert brackets[-1]["upper"] is None


def test_v2_unsupported_year_is_404(client, monkeypatch):
    roll(monkeypatch, 2)
    assert client.get("/tax-calculator/v2/tax-year/1999").status_code == 404


def test_credits_for_supported_year(client, monkeypatch):
    roll(monkeypatch, 2)
    resp = client.get("/tax-calculator/tax-year/2022/credits")
    assert resp.status_code == 200
    assert resp.json["deductions"][0]["code"] == "RRSP"
    assert resp.json["credits"][0] == {
        "code": "BASIC_PERSONAL",
        "description": "Basic personal credit, subtracted from the tax (the tax can't go below 0)",
        "amount": 2159.7,
        "refundable": False,
    }


def test_credits_unsupported_year_is_404(client, monkeypatch):
    roll(monkeypatch, 2)
    assert client.get("/tax-calculator/tax-year/1999/credits").status_code == 404


def test_correlation_id_is_echoed(client, monkeypatch):
    roll(monkeypatch, 2)
    resp = client.get("/tax-calculator/tax-year/2022", headers={"X-Correlation-ID": "abc-123"})
    assert resp.headers["X-Correlation-ID"] == "abc-123"
    assert "X-Correlation-ID" not in client.get("/tax-calculator/tax-year/2022").headers


def api_routes():
    return {
        r.rule.replace("<", "{").replace(">", "}")
        for r in server.app.url_map.iter_rules()
        if r.rule.startswith("/tax-calculator/")
    }


def test_full_spec_matches_routes(client):
    assert set(client.get("/openapi-full.json").json["paths"]) == api_routes()


def test_public_spec_has_baseline_only(client):
    spec = client.get("/openapi.json").json
    assert set(spec["paths"]) == {"/tax-calculator/tax-year/{tax_year}"}
    assert "securitySchemes" not in spec["components"]
    assert "Correlation" not in json.dumps(spec)


def test_docs_are_served(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/docs/full").status_code == 200
    assert client.get("/docs/").status_code == 200


def test_starter_zip_matches_tracked_starter_files(client):
    repo = Path(server.ROOT).parent
    try:
        tracked = subprocess.run(
            ["git", "-C", str(repo), "ls-files", "starter"], capture_output=True, text=True, check=True
        ).stdout.split()
    except (OSError, subprocess.CalledProcessError):
        pytest.skip("needs a git checkout")
    resp = client.get("/starter.zip")
    assert resp.status_code == 200
    with zipfile.ZipFile(server.STATIC / "starter.zip") as zf:
        files = {n: zf.read(n) for n in zf.namelist() if not n.endswith("/")}
    assert set(files) == set(tracked), "run ./build_starter_zip.sh"
    for name, data in files.items():
        assert data == (repo / name).read_bytes(), f"{name} changed, run ./build_starter_zip.sh"
