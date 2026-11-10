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
